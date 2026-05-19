{% extends "base.html" %}
{% block content %}
<div class="row justify-content-center mt-5">
    <div class="col-md-4">
        <div class="card">
            <div class="card-body">
                <h3 class="text-center mb-4">🔐 Login</h3>
                <form method="POST">
                    <div class="mb-3">
                        <label class="form-label">Usuário</label>
                        <input type="text" class="form-control" name="username" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Senha</label>
                        <input type="password" class="form-control" name="password" required>
                    </div>
                    <button type="submit" class="btn btn-primary w-100">Entrar</button>
                </form>
                <div class="text-center mt-3">
                    <small><a href="{{ url_for('setup') }}">Primeiro acesso? Configure aqui</a></small>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
