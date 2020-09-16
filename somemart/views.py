import json
from json import JSONDecodeError

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from .models import Item, Review

from django import forms

class NewCharField(forms.CharField):
    def to_python(self, value):
        if type(value) != str:
            raise ValidationError(
                (f'Invalid value: {value}'),
                code='invalid',
                params={'value': '42'},
            )
        else:
            return value

class ItemForm(forms.Form):
    title = NewCharField(min_length=1, max_length=64, required=True)
    description = NewCharField(min_length=1, max_length=1024, required=True)
    price = forms.IntegerField(min_value=1, max_value=1000000, required=True)


class ReviewForm(forms.Form):
    text = NewCharField(min_length=1, max_length=1024)
    grade = forms.IntegerField(min_value=1, max_value=10)


class GetItemView(View):
    """View для получения информации о товаре.
    Помимо основной информации выдает последние отзывы о товаре, не более 5
    штук.
    """
    def get(self, request, item_id):
        # Здесь должен быть ваш код

        try:
            item = Item.objects.get(pk=item_id)
        except ObjectDoesNotExist:
            return JsonResponse({"error": f"Товара с таким {item_id} не существует"}, status=404)

        data = {"id": item.pk, "title": item.title, "description": item.description, "price": item.price}
        reviews = Review.objects.all().filter(item_id=item_id).order_by('-id')[:5] or []
        try:
            temp_list = [(review.pk, review.text, review.grade) for review in reviews]
            keys = ("id", "text", "grade")
            data['reviews'] = [dict(zip(keys, values)) for values in temp_list]
        except (KeyError, ValueError):
            data['reviews'] = []
        return JsonResponse(data, status=200)




@method_decorator(csrf_exempt, name='dispatch')
class PostReviewView(View):
    """View для создания отзыва о товаре."""

    def post(self, request, item_id):
        if request.method == 'POST':
            try:
                request_data = json.loads(request.read())
            except (AttributeError, JSONDecodeError) as err:
                return JsonResponse({"error": err}, status=400)
            try:
                form = ReviewForm(request_data)
            except (Exception, forms.ValidationError) as val_err:
                print(f'{val_err} in {request}')
                return JsonResponse({}, status=400)
            if form.is_valid():
                try:
                    item = Item.objects.get(pk=item_id)
                    review = Review(item=item, text=request_data['text'], grade=request_data['grade'])
                    review.save()
                except ObjectDoesNotExist as ex:
                    return JsonResponse({"error": f"{ex}"}, status=404)
                return JsonResponse({"id": review.pk}, status=201)
            else:
                return JsonResponse({"error": "Invalid format"}, status=400)
        else:
            return JsonResponse({}, status=400)


@method_decorator(csrf_exempt, name='dispatch')
class AddItemView(View):
    """View для создания товара."""

    def post(self, request):
        # Здесь должен быть ваш код

        if request.method == 'POST':
            try:
                request_data = json.loads(request.read())
            except (AttributeError, JSONDecodeError) as err:

                print(err)
                return JsonResponse({}, status=400)
            try:
                print(request_data)
                item_form = ItemForm(request_data)
            except forms.ValidationError as val_err:
                print(f'{val_err} in {request}')
                return JsonResponse({}, status=400)

            if item_form.is_valid():
                data = item_form.cleaned_data
                item = Item.objects.create(title=data['title'], description=data['description'], price=data['price'])
                return JsonResponse({"id": item.pk}, status=201)
            else:
                return JsonResponse({}, status=400)
        else:
            return JsonResponse({}, status=400)