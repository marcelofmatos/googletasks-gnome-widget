#!/usr/bin/env python3
"""Google Tasks Desktop Widget — clicável, tema escuro, GNOME"""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GLib, Pango

import threading, webbrowser, os
from datetime import datetime, timezone

# ── Configuração ──────────────────────────────────────────────
WIDGET_WIDTH     = 340
REFRESH_SECONDS  = 300
CONFIG_DIR       = os.path.expanduser("~/.config/googletasks-widget")
CREDENTIALS_FILE = os.path.join(CONFIG_DIR, "credentials.json")
TOKEN_FILE       = os.path.join(CONFIG_DIR, "token.json")
SCOPES           = ["https://www.googleapis.com/auth/tasks"]

# ── Google API libs ───────────────────────────────────────────
try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request as GRequest
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    GOOGLE_LIBS_OK = True
except ImportError:
    GOOGLE_LIBS_OK = False


class NeedsAuthError(Exception):
    pass

_CELEBRATION_FRAMES = [
    "🎉  Tarefa concluída!  ✅",
    "✨  Tarefa concluída!  🌟",
    "🎊  Tarefa concluída!  🎉",
    "🌟  Tarefa concluída!  ✨",
    "🎈  Tarefa concluída!  🎊",
]

# Cores por lista (cicladas)
LIST_COLORS = [
    "#4db8ff",  # azul
    "#6bcb77",  # verde
    "#c56cf0",  # roxo
    "#ff9f43",  # laranja
    "#4ecdc4",  # teal
    "#ffd93d",  # amarelo
    "#ff6b6b",  # vermelho
]

CSS = b"""
window {
    background-color: rgba(8, 8, 18, 0.97);
    border-radius: 8px;
}
.widget-title {
    color: #4db8ff;
    font-weight: bold;
    font-size: 13px;
    padding: 10px 14px 2px 14px;
    letter-spacing: 1px;
}
.meta-label {
    color: #555577;
    font-size: 10px;
    padding: 0 14px 8px 14px;
}
.list-header {
    font-weight: bold;
    font-size: 10px;
    padding: 6px 14px 3px 14px;
    letter-spacing: 1.5px;
}
.task-row {
    margin: 1px 8px;
}
.task-row-new {
    background-color: rgba(77, 184, 255, 0.10);
    border-radius: 5px;
    transition: background-color 1200ms ease;
}
.task-btn {
    background: transparent;
    border: none;
    border-radius: 5px;
    margin: 0;
    padding: 0;
}
.task-btn:hover {
    background: rgba(255, 255, 255, 0.07);
}
.complete-btn {
    background: transparent;
    border: none;
    border-radius: 50%;
    color: #333355;
    font-size: 16px;
    min-width: 26px;
    min-height: 26px;
    padding: 0;
    margin: 0 2px 0 6px;
}
.complete-btn:hover {
    color: #6bcb77;
    background: rgba(107, 203, 119, 0.12);
}
.complete-btn:disabled {
    color: #555577;
    background: transparent;
}
.celebration-bar {
    font-size: 11px;
    font-weight: bold;
    padding: 5px 14px;
    border-top: 1px solid transparent;
    border-bottom: 1px solid transparent;
    color: transparent;
}
.celebration-active {
    color: #6bcb77;
    background: rgba(107, 203, 119, 0.08);
    border-top: 1px solid rgba(107, 203, 119, 0.25);
    border-bottom: 1px solid rgba(107, 203, 119, 0.25);
}
.task-inner {
    padding: 5px 8px;
}
.task-title {
    color: #bbbbbb;
    font-size: 11px;
}
.task-due-overdue { color: #ff6b6b; font-size: 10px; }
.task-due-today   { color: #ffd93d; font-size: 10px; }
.task-due-soon    { color: #ff9f43; font-size: 10px; }
.task-due-normal  { color: #555577; font-size: 10px; }
.sep {
    background-color: rgba(60, 60, 100, 0.35);
    margin: 3px 14px;
    min-height: 1px;
}
scrollbar {
    background: transparent;
    border: none;
}
scrollbar slider {
    background: rgba(100, 100, 160, 0.4);
    border-radius: 4px;
    min-width: 4px;
    min-height: 4px;
}
.error-label {
    color: #ff6b6b;
    font-size: 11px;
    padding: 8px 14px;
}
.auth-btn {
    background: rgba(77, 184, 255, 0.15);
    border: 1px solid rgba(77, 184, 255, 0.4);
    border-radius: 6px;
    color: #4db8ff;
    font-size: 11px;
    padding: 6px 12px;
    margin: 4px 14px;
}
.auth-btn:hover {
    background: rgba(77, 184, 255, 0.25);
}
.auth-btn:disabled {
    color: #555577;
    border-color: rgba(85, 85, 119, 0.4);
    background: transparent;
}
"""

# ── Helpers ───────────────────────────────────────────────────

def load_credentials():
    """Carrega/renova token salvo — sem abrir navegador.
    Lança NeedsAuthError se autenticação interativa for necessária."""
    if not GOOGLE_LIBS_OK:
        raise ImportError(
            "Dependências ausentes.\n"
            "pip install --user google-api-python-client "
            "google-auth-oauthlib google-auth-httplib2"
        )
    # Sem credentials.json não é possível autenticar — mostra botão
    if not os.path.exists(CREDENTIALS_FILE):
        raise NeedsAuthError("no_credentials")

    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        # Se o token foi criado com escopos menores (ex: tasks.readonly),
        # apaga e força re-autenticação com os escopos corretos
        token_scopes = set(creds.scopes or [])
        if token_scopes and not set(SCOPES).issubset(token_scopes):
            os.remove(TOKEN_FILE)
            raise NeedsAuthError()

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(GRequest())
                with open(TOKEN_FILE, "w") as f:
                    f.write(creds.to_json())
            except Exception:
                raise NeedsAuthError()
        else:
            raise NeedsAuthError()

    return creds


def run_oauth_flow():
    """Executa o fluxo OAuth2 interativo (abre navegador). Retorna Credentials."""
    if not os.path.exists(CREDENTIALS_FILE):
        raise FileNotFoundError(
            f"credentials.json não encontrado em:\n{CREDENTIALS_FILE}\n\n"
            "Baixe em: console.cloud.google.com\n"
            "APIs & Services → Credentials → OAuth 2.0 Client (Desktop app)"
        )
    flow  = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
    creds = flow.run_local_server(port=0)
    with open(TOKEN_FILE, "w") as f:
        f.write(creds.to_json())
    return creds


def fetch_all_tasks(service):
    """Busca todas as tarefas pendentes de todas as listas."""
    lists_result = service.tasklists().list(maxResults=20).execute()
    task_lists   = lists_result.get("items", [])

    result = []
    for tl in task_lists:
        resp  = service.tasks().list(
            tasklist=tl["id"],
            showCompleted=False,
            showHidden=False,
            maxResults=100,
        ).execute()
        tasks = [t for t in resp.get("items", []) if t.get("status") == "needsAction"]
        # ordena: com data de vencimento primeiro (mais próximas antes), depois sem data
        def sort_key(t):
            due = t.get("due")
            return (0, due) if due else (1, "")
        tasks.sort(key=sort_key)
        if tasks:
            result.append({"list": tl, "tasks": tasks})

    return result


def parse_due(due_str):
    """Converte string RFC 3339 da API do Google Tasks para date."""
    if not due_str:
        return None
    try:
        return datetime.fromisoformat(due_str.replace("Z", "+00:00")).date()
    except Exception:
        return None


# ── Widget principal ──────────────────────────────────────────

class GoogleTasksWidget(Gtk.Window):

    def __init__(self):
        super().__init__()
        self._service = None
        self._known_task_ids: set = set()
        self._setup_window()
        self._setup_css()
        self._build_skeleton()
        self.show_all()
        self._schedule_refresh()

    # ── Janela ────────────────────────────────────────────────

    def _setup_window(self):
        self.set_title("Google Tasks Widget")
        self.set_decorated(False)
        self.set_resizable(False)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_keep_below(True)
        self.stick()
        self.set_type_hint(Gdk.WindowTypeHint.DOCK)

        screen = self.get_screen()
        visual  = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)
        self.set_app_paintable(True)
        self.connect("draw", self._on_draw)

        mon   = Gdk.Display.get_default().get_primary_monitor()
        geom  = mon.get_geometry()
        scale = mon.get_scale_factor()
        w     = geom.width  // scale
        h     = geom.height // scale
        # Posiciona à esquerda do jira-widget (320px) + margem direita (20) + gap (10)
        self.move(w - WIDGET_WIDTH - 320 - 20 - 10, 50)
        self._screen_height = h
        # Altura fixa igual à do jira-widget: scroll (min(h-120,860)) + cabeçalho
        scroll_h = min(h - 120, 860)
        self.set_default_size(WIDGET_WIDTH, scroll_h + 80)
        self.set_size_request(WIDGET_WIDTH, scroll_h + 80)

        self.connect("destroy", Gtk.main_quit)

    def _on_draw(self, widget, cr):
        cr.set_source_rgba(0.031, 0.031, 0.071, 0.82)
        cr.paint()
        return False

    def _setup_css(self):
        provider = Gtk.CssProvider()
        provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    # ── Esqueleto fixo da UI ──────────────────────────────────

    def _build_skeleton(self):
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(root)

        title_btn = Gtk.Button()
        title_btn.set_relief(Gtk.ReliefStyle.NONE)
        title_lbl = Gtk.Label(label="☑  GOOGLE TASKS")
        title_lbl.set_halign(Gtk.Align.START)
        title_lbl.get_style_context().add_class("widget-title")
        title_btn.add(title_lbl)
        title_btn.connect("clicked", lambda _: webbrowser.open("https://tasks.google.com/"))
        root.pack_start(title_btn, False, False, 0)

        self.meta_lbl = Gtk.Label(label="   carregando…")
        self.meta_lbl.set_halign(Gtk.Align.START)
        self.meta_lbl.get_style_context().add_class("meta-label")
        root.pack_start(self.meta_lbl, False, False, 0)

        # Barra de celebração (espaço sempre reservado, sem deslocar a lista)
        self._celebration_lbl = Gtk.Label(label="")
        self._celebration_lbl.get_style_context().add_class("celebration-bar")
        root.pack_start(self._celebration_lbl, False, False, 0)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        max_h  = self._screen_height - 120
        scroll.set_size_request(WIDGET_WIDTH, min(max_h, 860))

        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        scroll.add(self.content)
        root.pack_start(scroll, True, True, 0)

    # ── Refresh ───────────────────────────────────────────────

    def _schedule_refresh(self):
        threading.Thread(target=self._fetch_and_update, daemon=True).start()

    def _fetch_and_update(self):
        try:
            creds = load_credentials()
            if self._service is None:
                self._service = build("tasks", "v1", credentials=creds)
            data = fetch_all_tasks(self._service)
            GLib.idle_add(self._render, data)
        except NeedsAuthError as e:
            GLib.idle_add(self._render_auth_required, str(e))
        except Exception as e:
            GLib.idle_add(self._render_error, str(e))

    # ── Auth flow ─────────────────────────────────────────────

    def _render_auth_required(self, reason=""):
        self._clear()
        self.meta_lbl.set_text("   autenticação necessária")

        if reason == "no_credentials":
            msg = (
                "1. Clique no botão abaixo\n"
                "2. Crie um projeto e ative\n"
                "    a Google Tasks API\n"
                "3. Vá em Credentials → Create\n"
                "    Credentials → OAuth client ID\n"
                "    (tipo: Desktop app)\n"
                "4. Baixe o credentials.json e\n"
                f"    salve em {CONFIG_DIR}/\n"
                "5. Reinicie o widget"
            )
            btn_label = "🌐  Abrir Google Cloud Console"
        else:
            msg = "Conecte sua conta Google\npara exibir as tarefas."
            btn_label = "🔑  Autentique-se"

        lbl = Gtk.Label(label=msg)
        lbl.set_justify(Gtk.Justification.LEFT)
        lbl.get_style_context().add_class("error-label")
        lbl.set_margin_top(12)
        self.content.pack_start(lbl, False, False, 0)

        self._auth_btn = Gtk.Button(label=btn_label)
        self._auth_btn.get_style_context().add_class("auth-btn")
        self._auth_btn.connect("clicked", self._on_auth_clicked)
        self.content.pack_start(self._auth_btn, False, False, 0)

        self.content.show_all()
        return False

    def _on_auth_clicked(self, button):
        if not os.path.exists(CREDENTIALS_FILE):
            webbrowser.open("https://console.cloud.google.com/apis/credentials")
            return
        button.set_sensitive(False)
        button.set_label("Abrindo navegador…")
        self.meta_lbl.set_text("   aguardando autorização…")
        threading.Thread(target=self._do_oauth, daemon=True).start()

    def _do_oauth(self):
        try:
            creds         = run_oauth_flow()
            self._service = build("tasks", "v1", credentials=creds)
            data          = fetch_all_tasks(self._service)
            GLib.idle_add(self._render, data)
        except FileNotFoundError as e:
            GLib.idle_add(self._render_auth_required, "no_credentials")
        except Exception as e:
            GLib.idle_add(self._render_error, str(e))

    # ── Renderização ──────────────────────────────────────────

    def _clear(self):
        for child in self.content.get_children():
            self.content.remove(child)

    def _render(self, data):
        self._clear()

        today = datetime.now(timezone.utc).date()
        now   = datetime.now().strftime('%H:%M')
        total = sum(len(item["tasks"]) for item in data)
        self._pending_count = total

        self.meta_lbl.set_text(f"   {now}  •  {total} tarefas pendentes")

        # Detecta tarefas novas (não presentes no render anterior)
        current_ids  = {t.get("id", "") for item in data for t in item["tasks"]}
        is_first_load = not bool(self._known_task_ids)
        new_ids       = set() if is_first_load else (current_ids - self._known_task_ids)
        _stagger      = [0]  # contador mutável para escalonamento

        if not data:
            lbl = Gtk.Label(label="Nenhuma tarefa pendente!")
            lbl.get_style_context().add_class("meta-label")
            lbl.set_margin_top(20)
            self.content.pack_start(lbl, False, False, 0)
        else:
            for idx, item in enumerate(data):
                tl    = item["list"]
                tasks = item["tasks"]
                color = LIST_COLORS[idx % len(LIST_COLORS)]

                # Cabeçalho da lista
                hdr = Gtk.Label()
                hdr.set_markup(
                    f'<span foreground="{color}" weight="bold" size="medium"'
                    f' letter_spacing="800">▸ {tl["title"].upper()}  ({len(tasks)})</span>'
                )
                hdr.set_halign(Gtk.Align.START)
                hdr.get_style_context().add_class("list-header")
                self.content.pack_start(hdr, False, False, 0)

                for task in tasks:
                    is_new = task.get("id", "") in new_ids
                    self.content.pack_start(
                        self._make_task_row(
                            task, color, today, tl["id"],
                            is_new=is_new, stagger_idx=_stagger[0]
                        ),
                        False, False, 0
                    )
                    if is_new:
                        _stagger[0] += 1

                sep = Gtk.Box()
                sep.get_style_context().add_class("sep")
                sep.set_size_request(-1, 1)
                self.content.pack_start(sep, False, False, 4)

        self._known_task_ids = current_ids
        self.content.show_all()
        GLib.timeout_add_seconds(REFRESH_SECONDS, self._on_timer)
        return False

    def _on_timer(self):
        self._schedule_refresh()
        return False  # não repetir — _render reagenda

    def _render_error(self, msg):
        self._clear()

        api_not_enabled = "has not been used" in msg or "disabled" in msg

        if api_not_enabled:
            text = (
                "Google Tasks API não está ativada\n"
                "no seu projeto do Google Cloud.\n\n"
                "Clique para ativá-la:"
            )
        else:
            text = f"Erro ao carregar tarefas:\n{msg[:160]}"

        lbl = Gtk.Label(label=text)
        lbl.set_line_wrap(True)
        lbl.set_xalign(0)
        lbl.get_style_context().add_class("error-label")
        self.content.pack_start(lbl, False, False, 0)

        if api_not_enabled:
            btn = Gtk.Button(label="⚡  Ativar Google Tasks API")
            btn.get_style_context().add_class("auth-btn")
            btn.connect("clicked", lambda _: webbrowser.open(
                "https://console.cloud.google.com/apis/library/tasks.googleapis.com"
            ))
            self.content.pack_start(btn, False, False, 0)
        else:
            retry_btn = Gtk.Button(label="🔄  Tentar novamente")
            retry_btn.get_style_context().add_class("auth-btn")
            retry_btn.connect("clicked", lambda _: self._schedule_refresh())
            self.content.pack_start(retry_btn, False, False, 0)

        self.content.show_all()
        GLib.timeout_add_seconds(60, self._on_timer)
        return False

    def _make_task_row(self, task, list_color, today, tasklist_id, *, is_new=False, stagger_idx=0):
        title   = task.get("title", "(sem título)")
        task_id = task.get("id", "")
        due     = parse_due(task.get("due"))

        if len(title) > 38:
            title = title[:35] + "…"

        # Linha externa: botão concluir + conteúdo da tarefa
        outer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        outer.get_style_context().add_class("task-row")

        # Botão concluir (○)
        complete_btn = Gtk.Button(label="○")
        complete_btn.get_style_context().add_class("complete-btn")
        outer.pack_start(complete_btn, False, False, 0)

        # Botão da tarefa (abre navegador)
        task_btn = Gtk.Button()
        task_btn.set_relief(Gtk.ReliefStyle.NONE)
        task_btn.get_style_context().add_class("task-btn")

        inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        inner.get_style_context().add_class("task-inner")

        title_lbl = Gtk.Label(label=title)
        title_lbl.set_halign(Gtk.Align.START)
        title_lbl.set_xalign(0)
        title_lbl.set_line_wrap(True)
        title_lbl.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        title_lbl.get_style_context().add_class("task-title")
        inner.pack_start(title_lbl, False, False, 0)

        if due:
            delta = (due - today).days
            if delta < 0:
                due_text  = f"⚠  venceu há {-delta}d  ({due.strftime('%d/%m')})"
                due_class = "task-due-overdue"
            elif delta == 0:
                due_text  = f"⏰  vence hoje  ({due.strftime('%d/%m')})"
                due_class = "task-due-today"
            elif delta <= 3:
                due_text  = f"📅  vence em {delta}d  ({due.strftime('%d/%m')})"
                due_class = "task-due-soon"
            else:
                due_text  = f"📅  {due.strftime('%d/%m/%Y')}"
                due_class = "task-due-normal"
            due_lbl = Gtk.Label(label=due_text)
            due_lbl.set_halign(Gtk.Align.START)
            due_lbl.get_style_context().add_class(due_class)
            inner.pack_start(due_lbl, False, False, 0)

        task_btn.add(inner)
        task_btn.connect("clicked", lambda _: webbrowser.open("https://tasks.google.com/"))
        outer.pack_start(task_btn, True, True, 0)

        # Revealer para animação de slide
        revealer = Gtk.Revealer()
        revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        revealer.set_transition_duration(300)
        revealer.add(outer)

        if is_new:
            # Começa oculto e abre com delay escalonado
            revealer.set_reveal_child(False)
            delay = min(60 + stagger_idx * 110, 750)
            GLib.timeout_add(delay, lambda r=revealer: r.set_reveal_child(True) or False)
            # Destaque azul temporário que some após ~1.8s
            outer.get_style_context().add_class("task-row-new")
            GLib.timeout_add(
                delay + 1800,
                lambda o=outer: o.get_style_context().remove_class("task-row-new") or False
            )
        else:
            revealer.set_reveal_child(True)

        complete_btn.connect(
            "clicked", self._on_complete_clicked, revealer, task_id, tasklist_id
        )
        return revealer

    # ── Concluir tarefa ───────────────────────────────────────

    def _on_complete_clicked(self, button, revealer, task_id, tasklist_id):
        button.set_sensitive(False)
        button.set_label("…")
        threading.Thread(
            target=self._do_complete_task,
            args=(revealer, task_id, tasklist_id),
            daemon=True
        ).start()

    def _do_complete_task(self, revealer, task_id, tasklist_id):
        try:
            self._service.tasks().patch(
                tasklist=tasklist_id,
                task=task_id,
                body={"status": "completed"}
            ).execute()
            GLib.idle_add(self._animate_task_done, revealer)
        except Exception as e:
            GLib.idle_add(self._render_error, str(e))

    def _animate_task_done(self, revealer):
        # Slide-up: oculta o revealer
        revealer.set_reveal_child(False)
        # Atualiza contador
        self._pending_count = max(0, getattr(self, '_pending_count', 1) - 1)
        now = datetime.now().strftime('%H:%M')
        self.meta_lbl.set_text(
            f"   {now}  •  {self._pending_count} tarefas pendentes"
        )
        # Remove widget após a animação terminar
        GLib.timeout_add(320, lambda: self._remove_widget(revealer) or False)
        # Mostra celebração
        self._show_celebration()
        return False

    def _remove_widget(self, widget):
        parent = widget.get_parent()
        if parent:
            parent.remove(widget)
        return False

    # ── Celebração ────────────────────────────────────────────

    def _show_celebration(self):
        self._cel_tick = 0
        ctx = self._celebration_lbl.get_style_context()
        ctx.add_class("celebration-active")
        GLib.timeout_add(100, self._tick_celebration)

    def _tick_celebration(self):
        frames = _CELEBRATION_FRAMES
        self._celebration_lbl.set_text(frames[self._cel_tick % len(frames)])
        self._cel_tick += 1
        if self._cel_tick < len(frames) * 4:   # 4 ciclos × 5 frames ≈ 2s
            GLib.timeout_add(130, self._tick_celebration)
        else:
            GLib.timeout_add(400, self._hide_celebration)
        return False

    def _hide_celebration(self):
        self._celebration_lbl.set_text("")
        self._celebration_lbl.get_style_context().remove_class("celebration-active")
        return False


# ── Entrypoint ────────────────────────────────────────────────

if __name__ == "__main__":
    os.makedirs(CONFIG_DIR, exist_ok=True)
    widget = GoogleTasksWidget()
    Gtk.main()
