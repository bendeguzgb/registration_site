from django.contrib.auth import login, logout
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.generic import UpdateView, View, ListView
from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from .forms import NewVisitorForm, NewClientForm, LoginForm, UpdateVisitorForm, UpdateClientForm, VisitorAdminComment, \
    ClientAdminComment
from .models import User, AdminComment, RegistrationStatus, UserType

REG_FORM_KEY = "register_form"
ERROR_KEY = "error"
INVALID_FORM_MESSAGE = "Registration Error: Please check your information and try again."
LOGIN_FAILED_MESSAGE = "We could not find the email and password combination you entered."
FROM_EMAIL = "reg@reg.com"


def home(request):
    return render(request, "home.html")


class CustomLoginView(LoginView):
    form_class = LoginForm
    template_name = "reg/login.html"

    def get_success_url(self):
        user = self.request.user
        return user.get_absolute_url()


def logout_view(request):
    logout(request)
    return redirect(reverse("main:home"))


def visitor_register(request):
    context = {}

    if request.method != "POST":
        context[REG_FORM_KEY] = NewVisitorForm()
        return render(request, "reg/visitor_register.html", context=context)

    form = NewVisitorForm(request.POST)

    if not form.is_valid():
        context[ERROR_KEY] = INVALID_FORM_MESSAGE
        context[REG_FORM_KEY] = form
        return render(request, "reg/visitor_register.html", context=context)

    user = form.save()
    login(request, user)
    send_welcome_email(user.email)

    return redirect(user.get_absolute_url())


def client_register(request):
    context = {}

    if request.method != "POST":
        context[REG_FORM_KEY] = NewClientForm()
        return render(request, "reg/client_register.html", context=context)

    form = NewClientForm(request.POST)

    if not form.is_valid():
        context[ERROR_KEY] = INVALID_FORM_MESSAGE
        context[REG_FORM_KEY] = form
        return render(request, "reg/client_register.html", context=context)

    user = form.save()
    login(request, user)
    send_welcome_email(user.email)

    return redirect(user.get_absolute_url())


class ProfileView(UserPassesTestMixin, View):
    template_name = "profile.html"

    def test_func(self):
        user_id = self.kwargs.get("pk")
        return self.request.user.id == user_id or self.request.user.is_superuser

    def handle_no_permission(self):
        return denied_not_found(self.request)

    def get_context_data(self, **kwargs):
        VIEWED_USER_KEY = "viewed_user"
        ADMIN_COMMENT_KEY = "admin_comment"
        HAS_PENDING_REG_STATUS_KEY = "has_pending_reg_status"

        user_id = self.kwargs.get("pk")
        current_user = self.request.user
        viewed_user = current_user if current_user.id == user_id else get_object_or_404(User, id=user_id)

        context = {
            VIEWED_USER_KEY: viewed_user,
            HAS_PENDING_REG_STATUS_KEY: viewed_user.registration_status == RegistrationStatus.PENDING,
        }

        if context[HAS_PENDING_REG_STATUS_KEY]:
            admin_comment, created = AdminComment.objects.get_or_create(user_id=user_id)
            context[ADMIN_COMMENT_KEY] = admin_comment

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        return render(request, self.template_name, context=context)


class UserInfoUpdateView(UpdateView):
    template_name = "user_info_update.html"
    queryset = User.objects.all()

    def get_object(self, queryset=None):
        return self.request.user

    def get_form_class(self):
        user = self.request.user

        if user.user_type == UserType.VISITOR:
            return UpdateVisitorForm
        else:
            return UpdateClientForm


class _AdminUserPassesTestMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return denied_not_found(self.request)


class _AdminBase(_AdminUserPassesTestMixin, View):
    template_name = None
    queryset = User.objects.all()

    def get_success_url(self):
        user = User.objects.get(id=self.kwargs["pk"])
        return user.get_absolute_url()

    def get_context_data(self, **kwargs):
        viewed_user = User.objects.get(id=self.kwargs["pk"])
        context = {"viewed_user": viewed_user}
        return context

    def get(self, *args, **kwargs):
        return render(self.request, self.template_name, context=self.get_context_data())


class AdminApprove(_AdminBase):
    template_name = "admin/admin_approve.html"

    def post(self, *args,  **kwargs):
        viewed_user: User = User.objects.get(id=self.kwargs["pk"])
        viewed_user.registration_status = RegistrationStatus.APPROVED
        viewed_user.save()
        send_approved_email(viewed_user.email)
        return redirect(viewed_user.get_absolute_url())


# class AdminCommentUpdateView(_AdminUserPassesTestMixin, UpdateView):
class AdminCommentUpdateView(UpdateView):
    template_name = "admin/admin_comment.html"
    queryset = AdminComment.objects.all()

    def get_object(self, queryset=None):
        return self.queryset.get(user_id=self.kwargs["pk"])

    def get_form_class(self):
        user = User.objects.get(id=self.kwargs["pk"])

        if user.user_type == UserType.VISITOR:
            return VisitorAdminComment
        else:
            return ClientAdminComment

    def get_context_data(self, **kwargs):
        viewed_user = User.objects.get(id=self.kwargs["pk"])
        context = super().get_context_data()
        context["viewed_user"] = viewed_user
        return context

    def get_success_url(self):
        viewed_user = User.objects.get(id=self.kwargs["pk"])
        send_admin_comment_email(viewed_user, self.queryset.get(user_id=viewed_user.id))
        return viewed_user.get_absolute_url()


class AdminReject(_AdminBase):
    template_name = "admin/admin_reject.html"

    def post(self, *args,  **kwargs):
        viewed_user: User = User.objects.get(id=self.kwargs["pk"])
        viewed_user.registration_status = RegistrationStatus.REJECTED
        viewed_user.is_active = False
        viewed_user.save()
        send_rejected_email(viewed_user.email)
        return redirect(viewed_user.get_absolute_url())


class AdminListView(_AdminUserPassesTestMixin, ListView):
    model = User
    template_name = 'admin/admin_list_users.html'
    context_object_name = 'users'
    paginate_by = 10
    max_page_size = 100

    def get_queryset(self):
        queryset = User.objects.all()

        page_size = self.request.GET.get('page_size', 10)
        self.paginate_by = min(int(page_size), self.max_page_size)

        first_name_filter = self.request.GET.get('first_name')
        last_name_filter = self.request.GET.get('last_name')
        status_filter = self.request.GET.get('status_filter')

        if first_name_filter:
            queryset = queryset.filter(first_name__icontains=first_name_filter)

        if last_name_filter:
            queryset = queryset.filter(first_name__icontains=last_name_filter)

        if status_filter and status_filter != "ALL":
            queryset = queryset.filter(registration_status=status_filter)

        return queryset


def denied_not_found(request, exception=None):
    return render(request, "denied_not_found.html", status=404)


def send_welcome_email(to: str):
    subject = "Registration received"
    plain_message = "Thank you for registering. \nYour request is still waiting for an Admin's approval."
    send_mail(subject, plain_message, FROM_EMAIL, (to,))


def send_admin_comment_email(viewed_user: User, admin_comment: AdminComment):
    template_name = "admin/admin_comment_email.html"
    subject = "Registration updated"
    to = [viewed_user.email]
    context = {
        "admin_comment": admin_comment,
        "is_client": viewed_user.user_type == UserType.CLIENT
    }

    html_message = render_to_string(template_name, context=context)
    plain_message = strip_tags(html_message)

    EmailMessage(subject, html_message, FROM_EMAIL, to)
    send_mail(subject, plain_message, FROM_EMAIL, to, html_message=html_message)


def send_rejected_email(to: str):
    subject = "Registration finalized"
    plain_message = "Unfortunately an Admin rejected your registration!"
    send_mail(subject, plain_message, FROM_EMAIL, (to,))


def send_approved_email(to: str):
    subject = "Registration finalized"
    plain_message = "Congratulations! An Admin approved your registration!"
    send_mail(subject, plain_message, FROM_EMAIL, (to,))
