from django.urls import reverse_lazy
from django.views import generic

from app_mailing.forms import AddNewRecipientForm
from app_mailing.models import Recipient


class RecipientListView(generic.ListView):
    """Представление для отображения страницы *recipient_list.html* со списком Получателей рассылки."""

    model = Recipient
    template_name = "app_mailing/recipient_list.html"
    context_object_name = "recipients"


class RecipientCreateView(generic.CreateView):
    """Представление для отображения страницы *recipient_add_update.html* с добавлением
    в список нового Получателя рассылки."""

    model = Recipient
    form_class = AddNewRecipientForm
    template_name = "app_mailing/recipient_add_update.html"
    success_url = reverse_lazy("app_mailing:recipient_list_page")


class RecipientDetailView(generic.DetailView):
    """."""

    pass


class RecipientUpdateView(generic.UpdateView):
    """Представление для отображения страницы *recipient_add_update.html* с возможностью редактирования
    Получателя рассылки из существующего списка."""

    model = Recipient
    form_class = AddNewRecipientForm
    template_name = "app_mailing/recipient_add_update.html"
    success_url = reverse_lazy("app_mailing:recipient_list_page")


class RecipientDeleteView(generic.DeleteView):
    """."""

    pass


# @method_decorator(cache_page(60 * 15), name="dispatch")  # Декоратор для создания кеша для всей страницы
# class CatalogDetailView(LoginRequiredMixin, DetailView):
#     """Представление для отображения страницы с подробной информацией о продукте (product.html)."""
#
#     model = Product
#     template_name = "catalog/product.html"
#     context_object_name = "product"
#
#
# class CatalogCreateView(LoginRequiredMixin, CreateView):
#     """Представление для отображения страницы с формой, которая позволяет пользователю добавлять новые товары в БД."""
#
#     model = Product
#     form_class = ProductForm
#     template_name = "catalog/add_your_product.html"
#     success_url = reverse_lazy("catalog:home_page")
#
#     def form_valid(self, form):
#         """1) Отправка пользователю уведомления о том, что его продукт успешно добавлен.
#         2) Автоматическое заполнение текущим пользователем поля 'owner' при создании нового продукта."""
#         form.instance.owner = self.request.user  # Привязываю текущего пользователя как owner
#         # С помощью стандартного механизма Django для уведомлений, отправляю пользователю сообщение
#         messages.success(self.request, f"Спасибо! Ваш продукт успешно добавлен.")
#         # Возвращаю стандартное поведение формы
#         return super().form_valid(form)
#
#     def get_form_kwargs(self):
#         """Передаю текущего пользователя в форму."""
#         kwargs = super().get_form_kwargs()
#         kwargs["initial"] = {"owner": self.request.user} # Передаём текущего пользователя, чтоб он сразу отображался
#         return kwargs
#
#
# class CatalogUpdateView(LoginRequiredMixin, UpdateView):
#     """Представление для редактирования продукта в магазине."""
#
#     model = Product
#     form_class = ProductForm
#     template_name = "catalog/add_your_product.html"
#
#     def dispatch(self, request, *args, **kwargs):
#         """Метод выполняет проверку прав пользователя на редактирование продукта (владелец продукта), заранее до
#         выполнения любого запроса (GET, POST и т.д.)."""
#         product = get_object_or_404(Product, pk=self.kwargs["pk"])
#         if not request.user == product.owner:
#             return HttpResponseForbidden(
#                 f"У вас нет прав для редактирования продукта. Обратитесь к владельцу: {product.owner}"
#             )
#         return super().dispatch(request, *args, **kwargs)
#
#     def get_success_url(self):
#         """Перенаправление на страницу с деталями продукта после успешного редактирования."""
#         return reverse("catalog:product_detail_page", kwargs={"pk": self.object.pk})
#
#     def form_valid(self, form):
#         """Метод сброса кеша продукта (CatalogDetailView) и списка продуктов в категории (CatalogCategoryProductsView)
#         после редактирования каких-либо параметров продукта."""
#         response = super().form_valid(form)
#
#         # Формирую URL и удаляю кеш для конкретного продукта (CatalogDetailView)
#         product_cache_url = reverse("catalog:product_detail_page", kwargs={"pk": self.object.pk})
#         cache.delete(product_cache_url)
#
#         # Формирую URL и удаляю кеш для списка продуктов (CatalogCategoryProductsView) с помощью сервисной функции
#         category_cache_key = f"category_products_{self.object.category.pk}"
#         cache.delete(category_cache_key)
#
#         return response
#
#
# class CatalogDeleteView(LoginRequiredMixin, DeleteView):
#     """Представление для удаления продукта в магазине."""
#
#     model = Product
#     template_name = "catalog/product_confirm_delete.html"
#     context_object_name = "product"
#     success_url = reverse_lazy("catalog:home_page")
#
#     object: Product  # Добавляю явную аннотацию чтоб не ругался MYPY
#
#     def dispatch(self, request, *args, **kwargs):
#         """Метод выполняет проверку прав пользователя на удаление продукта (владелец или модератор),
#         заранее до выполнения любого запроса (GET, POST и т.д.)."""
#         product = get_object_or_404(Product, pk=self.kwargs["pk"])
#         if request.user.has_perm("catalog.delete_product") or request.user == product.owner:
#             return super().dispatch(request, *args, **kwargs)
#         return HttpResponseForbidden(
#             f"У вас нет прав для удаления продукта. Обратитесь к владельцу ({product.owner}) или модераторам магазина."
#         )
#
#     def form_valid(self, form):
#         """Отправка пользователю уведомления о том, что продукт был удален."""
#         # Получаю объект продукт
#         product = self.get_object()
#         # С помощью стандартного механизма Django для уведомлений, отправляю пользователю сообщение
#         messages.success(self.request, f"Вы удалили продукт: {product.product_name}")
#         # Возвращаем стандартное поведение формы
#         return super().form_valid(form)
