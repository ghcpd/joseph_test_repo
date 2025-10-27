from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db.models import Q
from .models import User
import json


def index(request):
    return render(request, 'index.html')


def serialize_user(u: User):
    return {
        'id': u.id,
        'name': u.name,
        'email': u.email,
        'age': u.age,
        'gender': u.gender,
    }


@csrf_exempt
def users_list(request):
    if request.method == 'GET':
        page = int(request.GET.get('page', 1))
        size = int(request.GET.get('size', 10))
        search = request.GET.get('search')

        qs = User.objects.all().order_by('id')
        if search:
            qs = qs.filter(Q(name__icontains=search))

        total = qs.count()
        start = (page - 1) * size
        end = start + size
        users = [serialize_user(u) for u in qs[start:end]]
        return JsonResponse({'users': users, 'total': total, 'page': page, 'size': size})

    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError:
            return HttpResponseBadRequest('Invalid JSON')

        name = (data.get('name') or '').strip()
        email = (data.get('email') or '').strip()
        age = data.get('age')
        gender = (data.get('gender') or '').strip()

        errors = {}
        if not name:
            errors['name'] = 'Name cannot be empty'

        try:
            validate_email(email)
        except ValidationError:
            errors['email'] = 'Email is invalid'

        try:
            age = int(age)
            if age < 10 or age > 120:
                errors['age'] = 'Age must be between 10 and 120'
        except (TypeError, ValueError):
            errors['age'] = 'Age must be a number between 10 and 120'

        if gender not in [c[0] for c in User.Gender.choices]:
            errors['gender'] = 'Gender must be one of Male, Female, Other'

        if errors:
            return JsonResponse({'errors': errors}, status=400)

        if User.objects.filter(email=email).exists():
            return JsonResponse({'errors': {'email': 'Email already exists'}}, status=400)

        user = User.objects.create(name=name, email=email, age=age, gender=gender)
        return JsonResponse(serialize_user(user), status=201)

    return JsonResponse({'detail': 'Method not allowed'}, status=405)


@csrf_exempt
def user_delete(request, user_id: int):
    if request.method == 'DELETE':
        try:
            u = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({'detail': 'Not found'}, status=404)
        u.delete()
        return JsonResponse({'detail': 'Deleted'})

    return JsonResponse({'detail': 'Method not allowed'}, status=405)
