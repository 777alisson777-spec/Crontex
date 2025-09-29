from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

User = get_user_model()


class SignupForm(UserCreationForm):
    """
    Form de criação de usuário com validação de e-mail única (case-insensitive)
    e normalização básica. Mantém a validação de senha do Django.
    """
    username = forms.CharField(
        label="Usuário",
        strip=True,
        widget=forms.TextInput(attrs={"autocomplete": "username", "autocapitalize": "none"}),
    )
    email = forms.EmailField(
        label="E-mail",
        required=True,
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")
        help_texts = {
            "username": "",  # silencia help_text padrão do Django
        }

    def clean_username(self):
        username = (self.cleaned_data.get("username") or "").strip()
        # Opcional: travar espaços no username
        if " " in username:
            raise forms.ValidationError("O usuário não pode conter espaços.")
        return username

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        # Unicidade case-insensitive de e-mail
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Já existe um usuário com este e-mail.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        # Normaliza e aplica campos
        user.username = self.cleaned_data["username"].strip()
        user.email = self.cleaned_data["email"].strip().lower()
        if commit:
            user.save()
        return user
