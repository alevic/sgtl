import { FormEvent, useEffect, useState } from "react";

type Link = {
  id: number;
  titulo: string;
  url: string;
  ordem: number;
};

const API_URL =
  import.meta.env.VITE_API_URL ||
  (typeof window !== "undefined"
    ? `http://${window.location.hostname}:8000`
    : "http://127.0.0.1:8000");

function App() {
  const [links, setLinks] = useState<Link[]>([]);
  const [titulo, setTitulo] = useState("");
  const [url, setUrl] = useState("");
  const [token, setToken] = useState<string | null>(null);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [authError, setAuthError] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editingTitulo, setEditingTitulo] = useState("");
  const [editingUrl, setEditingUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [draggingId, setDraggingId] = useState<number | null>(null);

  const isPublicPage =
    typeof window !== "undefined" && window.location.pathname.includes("public");
  const isLoggedIn = Boolean(token);

  useEffect(() => {
    const savedToken = localStorage.getItem("biolinks_token");
    if (savedToken) {
      setToken(savedToken);
    }
  }, []);

  useEffect(() => {
    const fetchLinks = async () => {
      try {
        setLoading(true);
        const res = await fetch(`${API_URL}/links`);
        const data = await res.json();
        setLinks(data);
      } catch (err) {
        console.error(err);
        setError("Nao foi possivel carregar os links.");
      } finally {
        setLoading(false);
      }
    };
    fetchLinks();
  }, [token]);

  const handleLogin = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setAuthError(null);
    try {
      const res = await fetch(`${API_URL}/token`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({
          username,
          password
        })
      });
      if (!res.ok) {
        const maybeJson = await res.json().catch(() => null);
        const msg =
          typeof maybeJson?.detail === "string"
            ? maybeJson.detail
            : "Login falhou";
        throw new Error(msg);
      }
      const data = await res.json();
      setToken(data.access_token);
      localStorage.setItem("biolinks_token", data.access_token);
      setPassword("");
    } catch (err: any) {
      console.error(err);
      setAuthError(err?.message || "Login falhou");
    }
  };

  const handleLogout = () => {
    setToken(null);
    localStorage.removeItem("biolinks_token");
    setEditingId(null);
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    if (!token) {
      setError("Faça login para gerenciar links.");
      return;
    }

    try {
      const res = await fetch(`${API_URL}/links`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ titulo, url })
      });
      if (!res.ok) {
        const msg = await res.text();
        throw new Error(msg || "Erro desconhecido");
      }
      const newLink = (await res.json()) as Link;
      setLinks((prev) =>
        [...prev, newLink].sort((a, b) => a.ordem - b.ordem)
      );
      setTitulo("");
      setUrl("");
    } catch (err: any) {
      console.error(err);
      setError(err?.message || "Erro ao criar link. Verifique os dados.");
    }
  };

  const startEdit = (link: Link) => {
    setEditingId(link.id);
    setEditingTitulo(link.titulo);
    setEditingUrl(link.url);
  };

  const handleUpdate = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (editingId === null) return;
    setError(null);
    if (!token) {
      setError("Faça login para gerenciar links.");
      return;
    }
    const currentOrder =
      links.find((l) => l.id === editingId)?.ordem ?? links.length;

    try {
      const res = await fetch(`${API_URL}/links/${editingId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          titulo: editingTitulo,
          url: editingUrl,
          ordem: currentOrder
        })
      });
      if (!res.ok) {
        const msg = await res.text();
        throw new Error(msg || "Erro desconhecido");
      }
      const updated = (await res.json()) as Link;
      setLinks((prev) =>
        prev
          .map((l) => (l.id === updated.id ? updated : l))
          .sort((a, b) => a.ordem - b.ordem)
      );
      setEditingId(null);
    } catch (err: any) {
      console.error(err);
      setError(err?.message || "Erro ao atualizar link.");
    }
  };

  const handleDelete = async (id: number) => {
    setError(null);
    if (!token) {
      setError("Faça login para gerenciar links.");
      return;
    }
    try {
      const res = await fetch(`${API_URL}/links/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) {
        const msg = await res.text();
        throw new Error(msg || "Erro ao remover link");
      }
      setLinks((prev) => prev.filter((l) => l.id !== id));
      if (editingId === id) {
        setEditingId(null);
      }
    } catch (err: any) {
      console.error(err);
      setError(err?.message || "Erro ao remover link.");
    }
  };

  const reorderLocal = (sourceId: number, targetId: number) => {
    setLinks((prev) => {
      const src = prev.find((l) => l.id === sourceId);
      const tgt = prev.find((l) => l.id === targetId);
      if (!src || !tgt) return prev;
      const filtered = prev.filter((l) => l.id !== sourceId);
      const targetIndex = filtered.findIndex((l) => l.id === targetId);
      filtered.splice(targetIndex, 0, src);
      return filtered.map((l, idx) => ({ ...l, ordem: idx + 1 }));
    });
  };

  const persistOrder = async (ordered: Link[]) => {
    if (!token) return;
    try {
      const res = await fetch(`${API_URL}/links/reorder`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(ordered.map((l) => l.id))
      });
      if (!res.ok) {
        const msg = await res.text();
        throw new Error(msg || "Erro ao salvar ordem");
      }
    } catch (err: any) {
      console.error(err);
      setError(err?.message || "Erro ao salvar ordem.");
    }
  };

  const handleDragStart = (id: number) => setDraggingId(id);

  const handleDrop = (targetId: number) => {
    if (draggingId === null || draggingId === targetId) return;
    reorderLocal(draggingId, targetId);
    setDraggingId(null);
    setTimeout(() => {
      setLinks((curr) => {
        persistOrder(curr);
        return curr;
      });
    }, 0);
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-md space-y-6">
        <header className="text-center">
          <h1 className="text-3xl font-bold text-white">BioLinks</h1>
          <p className="text-sm text-gray-400">
            {isPublicPage ? "Página pública" : "Seu micro landing de links"}
          </p>
        </header>

        {!isPublicPage && (
          <form
            onSubmit={handleLogin}
            className="bg-gray-900/70 border border-gray-800 rounded-xl p-4 space-y-3 shadow-lg backdrop-blur"
          >
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-white">
                {isLoggedIn ? "Autenticado" : "Login"}
              </h2>
              {isLoggedIn && (
                <button
                  type="button"
                  onClick={handleLogout}
                  className="text-sm text-red-300 hover:text-red-100"
                >
                  Sair
                </button>
              )}
            </div>
            {!isLoggedIn && (
              <>
                <div className="flex flex-col space-y-1">
                  <label className="text-sm text-gray-300" htmlFor="login">
                    Usuário
                  </label>
                  <input
                    id="login"
                    name="login"
                    required
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-white focus:border-indigo-500 focus:outline-none"
                  />
                </div>
                <div className="flex flex-col space-y-1">
                  <label className="text-sm text-gray-300" htmlFor="password">
                    Senha
                  </label>
                  <input
                    id="password"
                    name="password"
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-white focus:border-indigo-500 focus:outline-none"
                  />
                </div>
                <button
                  type="submit"
                  className="w-full rounded-lg bg-indigo-500 px-4 py-2 font-semibold text-white shadow hover:bg-indigo-600 transition"
                >
                  Entrar
                </button>
                {authError && <p className="text-sm text-red-400">{authError}</p>}
              </>
            )}
          </form>
        )}

        {!isPublicPage && isLoggedIn && (
          <form
            onSubmit={editingId ? handleUpdate : handleSubmit}
            className="bg-gray-900/70 border border-gray-800 rounded-xl p-4 space-y-3 shadow-lg backdrop-blur"
          >
            <div className="flex flex-col space-y-1">
              <label className="text-sm text-gray-300" htmlFor="titulo">
                Título
              </label>
              <input
                id="titulo"
                name="titulo"
                required
                value={editingId ? editingTitulo : titulo}
                onChange={(e) =>
                  editingId
                    ? setEditingTitulo(e.target.value)
                    : setTitulo(e.target.value)
                }
                className="rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-white focus:border-indigo-500 focus:outline-none"
                placeholder="Meu site"
              />
            </div>

            <div className="flex flex-col space-y-1">
              <label className="text-sm text-gray-300" htmlFor="url">
                URL
              </label>
              <input
                id="url"
                name="url"
                type="text"
                required
                value={editingId ? editingUrl : url}
                onChange={(e) =>
                  editingId
                    ? setEditingUrl(e.target.value)
                    : setUrl(e.target.value)
                }
                className="rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-white focus:border-indigo-500 focus:outline-none"
                placeholder="https://..."
              />
            </div>

            <div className="flex space-x-2">
              <button
                type="submit"
                className="w-full rounded-lg bg-indigo-500 px-4 py-2 font-semibold text-white shadow hover:bg-indigo-600 transition"
              >
                {editingId ? "Salvar" : "Adicionar Link"}
              </button>
              {editingId && (
                <button
                  type="button"
                  onClick={() => setEditingId(null)}
                  className="w-full rounded-lg bg-gray-700 px-4 py-2 font-semibold text-white shadow hover:bg-gray-600 transition"
                >
                  Cancelar
                </button>
              )}
            </div>
            {error && <p className="text-sm text-red-400">{error}</p>}
          </form>
        )}

        {(isPublicPage || isLoggedIn) && (
          <section className="space-y-3">
            {loading ? (
              <p className="text-center text-gray-400">Carregando links...</p>
            ) : links.length === 0 ? (
              <p className="text-center text-gray-500">
                Nenhum link adicionado ainda.
              </p>
            ) : (
              links.map((link) => (
                <div
                  key={link.id}
                  draggable={!isPublicPage && isLoggedIn}
                  onDragStart={() => handleDragStart(link.id)}
                  onDragOver={(e) => {
                    e.preventDefault();
                    e.dataTransfer.dropEffect = "move";
                  }}
                  onDrop={() => handleDrop(link.id)}
                  className="flex items-center space-x-3 bg-gray-900/60 border border-gray-800 rounded-xl px-4 py-3 shadow cursor-grab"
                >
                  {!isPublicPage && isLoggedIn && (
                    <span className="text-sm text-gray-400 w-6 text-center">
                      {link.ordem}
                    </span>
                  )}
                  <a
                    href={link.url}
                    target="_blank"
                    rel="noreferrer"
                    className="flex-1 font-semibold text-white hover:text-indigo-400"
                  >
                    {link.titulo}
                  </a>
                  {!isPublicPage && isLoggedIn && (
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => startEdit(link)}
                        className="text-sm text-indigo-300 hover:text-indigo-100"
                      >
                        Editar
                      </button>
                      <button
                        onClick={() => handleDelete(link.id)}
                        className="text-sm text-red-400 hover:text-red-200"
                      >
                        Remover
                      </button>
                    </div>
                  )}
                </div>
              ))
            )}
          </section>
        )}
      </div>
    </div>
  );
}

export default App;
