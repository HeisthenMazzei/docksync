import random
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib import messages
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, FormView
from django.urls import reverse_lazy
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from core.mixins import GroupRequiredMixin

# ==========================================
# LOGIN (Customizado com Captcha)
# ==========================================
class CustomLoginView(View):
    template_name = 'registration/login.html'

    def get(self, request):
        num1 = random.randint(1, 9)
        num2 = random.randint(1, 9)
        captcha_texto = f"{num1} + {num2} = ?"
        captcha_esperado = num1 + num2
        return render(request, self.template_name, {
            'captcha_texto': captcha_texto,
            'captcha_esperado': captcha_esperado
        })

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        resposta = request.POST.get('captcha_resposta')
        esperado = request.POST.get('captcha_esperado')

        if not resposta or int(resposta) != int(esperado):
            messages.error(request, "Código de segurança incorreto.")
            num1 = random.randint(1, 9)
            num2 = random.randint(1, 9)
            captcha_texto = f"{num1} + {num2} = ?"
            captcha_esperado = num1 + num2
            return render(request, self.template_name, {
                'captcha_texto': captcha_texto,
                'captcha_esperado': captcha_esperado
            })

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Usuário ou senha incorretos.")
            num1 = random.randint(1, 9)
            num2 = random.randint(1, 9)
            captcha_texto = f"{num1} + {num2} = ?"
            captcha_esperado = num1 + num2
            return render(request, self.template_name, {
                'captcha_texto': captcha_texto,
                'captcha_esperado': captcha_esperado
            })

# ==========================================
# CRUD DE USUÁRIOS (Admin)
# ==========================================
class UsuarioListView(GroupRequiredMixin, ListView):
    model = User
    template_name = 'cadastro/usuario_list.html'
    context_object_name = 'usuarios'
    group_required = ['Administrador']
    def get_queryset(self):
        return User.objects.all().order_by('-date_joined')

class UsuarioCreateView(GroupRequiredMixin, CreateView):
    model = User
    template_name = 'cadastro/usuario_form.html'
    success_url = reverse_lazy('usuario_list')
    fields = ['username', 'first_name', 'last_name', 'email', 'password']
    group_required = ['Administrador']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grupos'] = Group.objects.all()
        context['is_edit'] = False
        return context

    def form_valid(self, form):
        user = form.save(commit=False)
        user.set_password(form.cleaned_data['password'])
        user.save()

        grupo_id = self.request.POST.get('grupo')
        if grupo_id:
            grupo = Group.objects.get(id=int(grupo_id))
            user.groups.add(grupo)

        messages.success(self.request, "Usuário cadastrado com sucesso!")
        return redirect('usuario_list')

# CORRIGIDO: Permitir alterar senha na edição
class UsuarioUpdateView(GroupRequiredMixin, UpdateView):
    model = User
    template_name = 'cadastro/usuario_form.html'
    success_url = reverse_lazy('usuario_list')
    fields = ['username', 'first_name', 'last_name', 'email']
    group_required = ['Administrador']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grupos'] = Group.objects.all()
        context['is_edit'] = True
        return context

    def form_valid(self, form):
        user = form.save(commit=False)

        # Se o campo de senha foi preenchido, altera a senha
        nova_senha = self.request.POST.get('nova_senha')
        if nova_senha:
            user.set_password(nova_senha)
        
        user.save()

        # Atualiza o grupo do usuário
        user.groups.clear()
        grupo_id = self.request.POST.get('grupo')
        if grupo_id:
            grupo = Group.objects.get(id=int(grupo_id))
            user.groups.add(grupo)

        messages.success(self.request, "Usuário atualizado com sucesso!")
        return redirect('usuario_list')

class UsuarioDeleteView(GroupRequiredMixin, DeleteView):
    model = User
    template_name = 'cadastro/confirm_delete_usuario.html'
    success_url = reverse_lazy('usuario_list')
    group_required = ['Administrador']

# ==========================================
# TROCA DE SENHA (Para o próprio usuário)
# ==========================================
@method_decorator(login_required, name='dispatch')
class TrocarSenhaView(FormView):
    template_name = 'cadastro/trocar_senha.html'
    form_class = PasswordChangeForm
    success_url = reverse_lazy('dashboard')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        user = form.save()
        update_session_auth_hash(self.request, user)
        messages.success(self.request, "Senha alterada com sucesso!")
        return super().form_valid(form)