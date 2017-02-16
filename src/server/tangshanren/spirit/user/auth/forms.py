# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from mine.models import user_mine
from vircurrency.models import VirAccount

from ..forms import CleanEmailMixin

User = get_user_model()


class RegistrationForm(CleanEmailMixin, forms.ModelForm):

    # email2 = forms.CharField(
    #     label=_("邮箱"),
    #     widget=forms.EmailInput,
    #     max_length=254,
    #     help_text=_("")
    # )
    # todo: add password validator for Django 1.9
    password = forms.CharField(label=_("密码"), widget=forms.PasswordInput)
    phone = forms.CharField(label=_("手机"), max_length=11)
    # honeypot = forms.CharField(label=_("Leave blank"), required=False)
    zone_id = forms.ChoiceField(label=_("地区"),choices=[('4','唐山市区'),('5','乐亭'),('6','滦南'),('7','迁安'),('8','丰南'),('9','唐海'),('10','遵化'),('11','迁西'),('13','丰润'),('15','滦县'),('16','玉田'),('17','开平')])  

    class Meta:
        model = User
        fields = ("username", "email")

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        self.fields['email'].required = True  # Django model does not requires it

    def clean_honeypot(self):
        """Check that nothing has been entered into the honeypot."""
        value = self.cleaned_data["honeypot"]

        if value:
            raise forms.ValidationError(_("Do not fill this field."))

        return value

    def clean_username(self):
        username = self.cleaned_data["username"]

        is_taken = User.objects\
            .filter(username=username)\
            .exists()

        if is_taken:
            raise forms.ValidationError(_("The username is taken."))

        return username

    def clean_email2(self):
        email = self.cleaned_data.get("email")
        email2 = self.cleaned_data["email2"]

        if settings.ST_CASE_INSENSITIVE_EMAILS:
            email2 = email2.lower()

        if email and email != email2:
            raise forms.ValidationError(
                _("The two email fields didn't match.")
            )

        return email2

    def save(self, commit=True):
        self.instance.is_active = True
        self.instance.set_password(self.cleaned_data["password"])

        mine = user_mine(username=self.cleaned_data["username"],locol_id=self.cleaned_data['zone_id'],phone=self.cleaned_data['phone'])
        mine.save()

        viruser = VirAccount(username=self.cleaned_data["username"])
        viruser.save()

        return super(RegistrationForm, self).save(commit)


class LoginForm(AuthenticationForm):

    username = forms.CharField(label=_("账号"), max_length=254)

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        self.error_messages['invalid_login'] = _("密码错误.")

    def _validate_username(self):
        """
        Check the username exists.\
        Show if the username or email is invalid\
        instead of the unclear "username or\
        password is invalid" message.
        """
        username = self.cleaned_data.get("username")

        if not username:
            return

        is_found = User.objects\
            .filter(username=username)\
            .exists()

        if is_found:
            return

        if settings.ST_CASE_INSENSITIVE_EMAILS:
            username = username.lower()

        is_found_email = User.objects\
            .filter(email=username)\
            .exists()

        if is_found_email:
            return

        raise forms.ValidationError(
            _("%(username)s 账户不存在.") % {'username': username}
        )

    def clean(self):
        self._validate_username()
        return super(LoginForm, self).clean()


class ResendActivationForm(forms.Form):

    email = forms.CharField(label=_("Email"), widget=forms.EmailInput, max_length=254)

    def clean_email(self):
        email = self.cleaned_data["email"]

        if settings.ST_CASE_INSENSITIVE_EMAILS:
            email = email.lower()

        is_existent = User.objects\
            .filter(email=email)\
            .exists()

        if not is_existent:
            raise forms.ValidationError(_("The provided email does not exists."))

        self.user = User.objects\
            .filter(email=email, st__is_verified=False)\
            .order_by('-pk')\
            .first()

        if not self.user:
            raise forms.ValidationError(_("This account is verified, try logging-in."))

        return email

    def get_user(self):
        return self.user
