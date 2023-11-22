from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm


from main.models import UserType, AdminComment

UserModel = get_user_model()


class _NewUserForm(UserCreationForm):
    first_name = forms.CharField(required=True, max_length=100)
    last_name = forms.CharField(required=True, max_length=100)
    email = forms.EmailField(required=True)
    phone_number = forms.RegexField(required=True,
                                    regex=r'^\+\d{9,15}$',
                                    help_text="Phone number must be entered in the format: '+0123456789'. Up to 15 digits are allowed.")


class NewVisitorForm(_NewUserForm):
    orcid_id = forms.RegexField(required=False, regex=r'^\d{4}-\d{4}-\d{4}-\d{4}$', help_text="ORCID id must be entered in the format: '0000-0001-2345-6789'")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = UserType.VISITOR
        if commit:
            user.save()
        return user

    class Meta:
        model = UserModel
        fields = ("first_name", "last_name", "phone_number", "email", "password1", "password2")


class NewClientForm(_NewUserForm):
    company_name = forms.CharField(required=True)
    country_of_origin = forms.CharField(required=True)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = UserType.CLIENT
        if commit:
            user.save()
        return user

    class Meta:
        model = UserModel
        fields = ("first_name", "last_name", "phone_number", "company_name", "country_of_origin", "email", "password1", "password2")


class UpdateVisitorForm(forms.ModelForm):
    class Meta:
        model = UserModel
        fields = ("first_name", "last_name", "phone_number")


class UpdateClientForm(forms.ModelForm):
    class Meta:
        model = UserModel
        fields = ("first_name", "last_name", "phone_number", "company_name", "country_of_origin")


class VisitorAdminComment(forms.ModelForm):
    class Meta:
        model = AdminComment
        fields = ("first_name", "last_name", "email", "phone_number")


class ClientAdminComment(forms.ModelForm):
    class Meta:
        model = AdminComment
        fields = ("first_name", "last_name", "email", "phone_number", "company_name", "country_of_origin")


class LoginForm(AuthenticationForm):
    username = forms.EmailField(widget=forms.EmailInput(attrs={"autofocus": True}))
