from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView
from django.urls import path, reverse_lazy

from users.views import (ActivateAccountView, AppUserListView, BlockUserView,
                         UnblockUserView, UserEmailConfirmationSentView,
                         UserLoginView, UserRegisterView, UserStartView)

app_name = "users"

urlpatterns = [
    path("start/", UserStartView.as_view(), name="start_page"),
    path("register/", UserRegisterView.as_view(), name="register_page"),
    path("activate/<uidb64>/<token>/", ActivateAccountView.as_view(), name="activate_account"),
    path("email-confirmation-sent/", UserEmailConfirmationSentView.as_view(), name="email_confirmation_sent_page"),
    path("login/", UserLoginView.as_view(), name="login_page"),
    path("logout/", LogoutView.as_view(), name="logout_page"),
    path("app-users/", AppUserListView.as_view(), name="user_list_page"),
    path("app-users/<int:pk>/block", BlockUserView.as_view(), name="block_user_page"),
    path("app-users/<int:pk>/unblock", UnblockUserView.as_view(), name="unblock_user_page"),
    # Часть для сброса пароля с использованием коробочного решения auth_views
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="users/password_reset/password_reset.html",
            # Django по умолчанию ищет коробочный шаблон в "registration/password_reset_email.html" и ожидает
            # стандартные имена URL-ов (password_reset_confirm и др.). Так как я изменил name= в urls.py
            # (сделал "name="password_reset_confirm_page""), то мне нужно использовать собственный шаблон письма
            # и указать свои url-имя в нём (email_template_name=).
            email_template_name="users/password_reset/email_confirm_reset.html",
            # Django по умолчанию в PasswordResetView ожидает, что путь для редиректа после успешной отправки email
            # будет называться коробочно вот так "password_reset_done", но я его изменил на "password_reset_done_page"
            # и поэтому необходимо это явно указать, чтоб не было ошибок.
            success_url=reverse_lazy("users:password_reset_done_page"),
        ),
        name="password_reset_page",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="users/password_reset/password_reset_done.html"
        ),
        name="password_reset_done_page",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="users/password_reset/password_reset_confirm.html",
            # Аналогично и для редиректа тут, чтобы после установки нового пароля была переадресация на
            # "users:password_reset_complete_page", а не на коробочное название, которое ожидает Django по умолчанию.
            success_url=reverse_lazy("users:password_reset_complete_page"),
        ),
        name="password_reset_confirm_page",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="users/password_reset/password_reset_complete.html"
        ),
        name="password_reset_complete_page",
    ),
]
