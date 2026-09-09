<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>⚡ FastFood POS Pro Web</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- Librería jsPDF para generación automática de PDF -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf-autotable/3.5.31/jspdf.plugin.autotable.min.js"></script>
    <style>
        body { background-color: #0f172a; color: #f8fafc; font-family: system-ui, -apple-system, sans-serif; }
        .card { background-color: #1e293b; border: 1px solid #334155; border-radius: 0.75rem; }
        .btn-primary { background-color: #10b981; color: white; font-weight: bold; }
        .btn-primary:hover { background-color: #059669; }
    </style>
</head>
<body class="h-screen flex flex-col">

    <!-- HEADER -->
    <header class="bg-slate-800 border-b border-slate-700 px-6 py-4 flex justify-between items-center">
        <h1 class="text-xl font-bold text-emerald-400">⚡ FastFood POS Pro</h1>
        <div id="userInfo" class="flex items-center gap-4 hidden">
            <span id="userBadge" class="text-sm font-semibold bg-slate-700 px-3 py-1 rounded-full"></span>
            <button onclick="logout()" class="bg-red-500 hover:bg-red-600 text-white text-xs px-3 py-1.5 rounded-lg font-bold">Cerrar Sesión</button>
        </div>
    </header>

    <!-- LOGIN SCREEN -->
    <div id="loginScreen" class="flex-1 flex items-center justify-center p-4">
        <div class="card p-8 w-full max-w-md shadow-xl text-center">
            <h2 class="text-2xl font-bold text-emerald-400 mb-1">⚡ FastFood POS</h2>
            <p class="text-slate-400 text-sm mb-6">Inicio de Sesión Centralizado</p>
            <form onsubmit="handleLogin(event)" class="space-y-4">
                <input type="text" id="loginUser" placeholder="Usuario" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-white focus:outline-none focus:border-emerald-500" required>
                <input type="password" id="loginPass" placeholder="Contraseña" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-white focus:outline-none focus:border-emerald-500" required>
                <button type="submit" class="w-full btn-primary p-3 rounded-lg">INGRESAR AL SISTEMA</button>
            </form>
            <p class="text-xs text-slate-500 mt-4">Demo: admin/admin, mesero1/1234, multi1/1234</p>
        </div>
    </div>

    <!-- MAIN APP SCREEN -->
    <div id="appScreen" class="flex-1 flex flex-col md:flex-row overflow-hidden hidden">
        
        <!-- SIDEBAR NAVEGACIÓN -->
        <nav id="sidebar" class="w-full md:w-64 bg-slate-800 p-4 border-r border-slate-700 flex md:flex-col gap-2 overflow-x-auto">
            <!-- Botones dinámicos según el rol -->
        </nav>

        <!-- CONTENIDO PRINCIPAL -->
        <main class="flex-1 p-6 overflow-y-auto">

            <!-- VISTA: TOMAR PEDIDO -->
            <section id="viewPedido" class="hidden">
                <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <div class="lg:col-span-2 space-y-4">
                        <div class="flex items-center gap-4 bg-slate-800 p-4 rounded-xl">
                            <label class="font-bold text-sm">📁 Sección:</label>
                            <select id="filterCategory" onchange="renderCatalog()" class="bg-slate-900 border border-slate-700 rounded-lg p-2 text-white"></select>
                        </div>
                        <div id="catalogGrid" class="grid grid-cols-2 sm:grid-cols-3 gap-4"></div>
                    </div>

                    <!-- CARRITO & DATOS DE FACTURACIÓN -->
                    <div class="card p-4 flex flex-col h-[680px]">
                        <h3 class="font-bold text-lg mb-2">Orden del Cliente</h3>
                        <input type="text" id="orderClient" placeholder="Cliente / Mesa" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-sm mb-2">
                        
                        <!-- DATOS OPCIONALES DE FACTURA -->
                        <div class="bg-slate-900 p-3 rounded-lg mb-2 space-y-2">
                            <span class="text-xs font-bold text-emerald-400 block">📄 Datos de Facturación (Opcional)</span>
                            <div class="grid grid-cols-2 gap-2">
                                <input type="text" id="factRuc" placeholder="RUC / Cédula" class="bg-slate-800 border border-slate-700 rounded p-1.5 text-xs">
                                <input type="text" id="factRazon" placeholder="Razón Social / Nombre" class="bg-slate-800 border border-slate-700 rounded p-1.5 text-xs">
                            </div>
                            <div class="grid grid-cols-2 gap-2">
                                <input type="text" id="factPhone" placeholder="Teléfono" class="bg-slate-800 border border-slate-700 rounded p-1.5 text-xs">
                                <input type="email" id="factEmail" placeholder="Correo Electrónico" class="bg-slate-800 border border-slate-700 rounded p-1.5 text-xs">
                            </div>
                        </div>

                        <!-- SECCIÓN ITEM LIBRE -->
                        <div class="bg-slate-900 p-2.5 rounded-lg mb-2">
                            <span class="text-xs font-bold text-purple-400 block mb-1">✨ Pedido Especial / Libre</span>
                            <div class="flex gap-2 mb-1">
                                <input type="text" id="customItemDesc" placeholder="Descripción" class="w-2/3 bg-slate-800 border border-slate-700 rounded p-1.5 text-xs">
                                <input type="number" id="customItemPrice" placeholder="Precio ($)" class="w-1/3 bg-slate-800 border border-slate-700 rounded p-1.5 text-xs">
                            </div>
                            <button onclick="addCustomItem()" class="w-full bg-purple-600 hover:bg-purple-700 text-xs font-bold p-1 rounded">Agregar Especial</button>
                        </div>

                        <!-- LISTA ITEMS EN CARRITO -->
                        <div id="cartItems" class="flex-1 overflow-y-auto space-y-1.5 mb-2 pr-1"></div>

                        <div class="border-t border-slate-700 pt-2 mt-auto">
                            <div class="flex justify-between items-center text-lg font-bold text-emerald-400 mb-2">
                                <span>TOTAL:</span>
                                <span id="cartTotal">$0.00</span>
                            </div>
                            <button onclick="submitOrder()" class="w-full btn-primary p-2.5 rounded-lg">🚀 REGISTRAR PEDIDO</button>
                        </div>
                    </div>
                </div>
            </section>

            <!-- VISTA: CAJA -->
            <section id="viewCaja" class="hidden space-y-4">
                <h2 class="text-2xl font-bold text-sky-400">💰 Panel de Cobros y Caja</h2>
                <div id="pendingOrders" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"></div>
            </section>

            <!-- VISTA: COCINA -->
            <section id="viewCocina" class="hidden space-y-4">
                <h2 class="text-2xl font-bold text-orange-400">🔥 Monitor de Cocina</h2>
                <div id="kitchenOrders" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"></div>
            </section>

            <!-- VISTA: REPORTES Y PDF CONTADORA -->
            <section id="viewReportes" class="hidden space-y-6">
                <div class="flex justify-between items-center flex-wrap gap-4">
                    <h2 class="text-2xl font-bold text-emerald-400">📊 Reportes y Facturación</h2>
                    <button onclick="exportContadoraPDF()" class="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg font-bold text-sm flex items-center gap-2">
                        📄 Descargar Reporte PDF para Contadora
                    </button>
                </div>
                
                <div class="card p-4 flex flex-wrap gap-4 items-center">
                    <label class="font-bold text-sm">📅 Filtrar por Fecha:</label>
                    <input type="date" id="reportDate" onchange="renderReports()" class="bg-slate-900 border border-slate-700 rounded-lg p-2 text-white">
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div class="card p-6 border-emerald-500 text-center">
                        <span class="text-slate-400 text-sm">Total Ventas Cobradas</span>
                        <div id="kpiTotal" class="text-3xl font-bold text-emerald-400 mt-2">$0.00</div>
                    </div>
                    <div class="card p-6 border-sky-500 text-center">
                        <span class="text-slate-400 text-sm">Cantidad de Pedidos</span>
                        <div id="kpiCount" class="text-3xl font-bold text-sky-400 mt-2">0</div>
                    </div>
                </div>

                <div class="card p-4">
                    <h3 class="font-bold mb-3 text-sky-400">💳 Desglose por Formas de Pago</h3>
                    <div id="paymentBreakdown" class="grid grid-cols-1 sm:grid-cols-3 gap-4"></div>
                </div>

                <div class="card p-4">
                    <h3 class="font-bold mb-3">📋 Historial de Ventas y Datos Fiscales</h3>
                    <div class="overflow-x-auto">
                        <table class="w-full text-left text-sm">
                            <thead class="bg-slate-700 text-slate-300">
                                <tr>
                                    <th class="p-2">ID</th>
                                    <th class="p-2">Fecha/Hora</th>
                                    <th class="p-2">Usuario</th>
                                    <th class="p-2">Cliente / Raz. Social</th>
                                    <th class="p-2">RUC / Cédula</th>
                                    <th class="p-2">Método Pago</th>
                                    <th class="p-2">Total</th>
                                    <th class="p-2">Estado</th>
                                </tr>
                            </thead>
                            <tbody id="reportTableBody" class="divide-y divide-slate-700"></tbody>
                        </table>
                    </div>
                </div>
            </section>

            <!-- VISTA: ADMIN CONFIGURACIÓN -->
            <section id="viewAdmin" class="hidden space-y-6">
                <h2 class="text-2xl font-bold text-purple-400">⚙️ Configuración del Sistema</h2>

                <div class="card p-6 space-y-4">
                    <h3 class="font-bold text-lg text-emerald-400">👥 Gestión de Usuarios y Personal</h3>
                    <div class="grid grid-cols-1 md:grid-cols-4 gap-3">
                        <input type="text" id="newFullName" placeholder="Nombre Completo" class="bg-slate-900 border border-slate-700 rounded p-2 text-sm">
                        <input type="text" id="newUsername" placeholder="Usuario (Login)" class="bg-slate-900 border border-slate-700 rounded p-2 text-sm">
                        <input type="password" id="newPassword" placeholder="Contraseña" class="bg-slate-900 border border-slate-700 rounded p-2 text-sm">
                        <select id="newRole" class="bg-slate-900 border border-slate-700 rounded p-2 text-sm text-white">
                            <option value="mesero">Mesero</option>
                            <option value="cocina">Cocina</option>
                            <option value="caja">Caja</option>
                            <option value="multitarea">Multitarea</option>
                            <option value="admin">Administrador</option>
                        </select>
                    </div>
                    <button onclick="addUser()" class="btn-primary px-4 py-2 rounded text-sm w-full md:w-auto">➕ Guardar Usuario</button>

                    <div class="overflow-x-auto mt-4">
                        <table class="w-full text-left text-sm">
                            <thead class="bg-slate-700 text-slate-300">
                                <tr>
                                    <th class="p-2">Nombre</th>
                                    <th class="p-2">Usuario</th>
                                    <th class="p-2">Rol / Cargo</th>
                                    <th class="p-2">Acción</th>
                                </tr>
                            </thead>
                            <tbody id="usersTableBody" class="divide-y divide-slate-700"></tbody>
                        </table>
                    </div>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div class="card p-4 space-y-3">
                        <h3 class="font-bold">📁 Secciones / Categorías</h3>
                        <div class="flex gap-2">
                            <input type="text" id="newCatName" placeholder="Nueva Sección" class="flex-1 bg-slate-900 border border-slate-700 rounded p-2 text-sm">
                            <button onclick="addCategory()" class="btn-primary px-4 py-2 rounded text-sm">Crear</button>
                        </div>
                        <ul id="catList" class="divide-y divide-slate-700 text-sm"></ul>
                    </div>

                    <div class="card p-4 space-y-3">
                        <h3 class="font-bold">🥫 Salsas y Términos</h3>
                        <div class="flex gap-2">
                            <input type="text" id="newSauceName" placeholder="Ej: BBQ, Picante, Bien Cocido" class="flex-1 bg-slate-900 border border-slate-700 rounded p-2 text-sm">
                            <button onclick="addSauce()" class="btn-primary px-4 py-2 rounded text-sm">Crear</button>
                        </div>
                        <ul id="sauceList" class="divide-y divide-slate-700 text-sm"></ul>
                    </div>
                </div>
            </section>
        </main>
    </div>

    <!-- MODAL SALSA -->
    <div id="sauceModal" class="fixed inset-0 bg-black/70 flex items-center justify-center p-4 hidden">
        <div class="card p-6 w-full max-w-md space-y-4">
            <h3 id="modalTitle" class="font-bold text-lg text-sky-400"></h3>
            <div>
                <label class="text-xs font-bold text-slate-400 block mb-1">Selecciona Salsa o Término:</label>
                <select id="modalSauceSelect" class="w-full bg-slate-900 border border-slate-700 rounded p-2 text-white"></select>
            </div>
            <div>
                <label class="text-xs font-bold text-slate-400 block mb-1">Nota adicional (Opcional):</label>
                <input type="text" id="modalNoteInput" placeholder="Ej: Bien crujiente" class="w-full bg-slate-900 border border-slate-700 rounded p-2 text-white">
            </div>
            <div class="flex gap-2 justify-end">
                <button onclick="closeSauceModal()" class="bg-slate-700 hover:bg-slate-600 px-4 py-2 rounded text-sm font-bold">Cancelar</button>
                <button onclick="confirmSauceModal()" class="btn-primary px-4 py-2 rounded text-sm">Agregar al Carrito</button>
            </div>
        </div>
    </div>

    <script>
        let db;
        const request = indexedDB.open("FastFoodPOS", 3);

        request.onupgradeneeded = (e) => {
            db = e.target.result;
            if (!db.objectStoreNames.contains("usuarios")) db.createObjectStore("usuarios", { keyPath: "usuario" });
            if (!db.objectStoreNames.contains("categorias")) db.createObjectStore("categorias", { keyPath: "id", autoIncrement: true });
            if (!db.objectStoreNames.contains("salsas")) db.createObjectStore("salsas", { keyPath: "id", autoIncrement: true });
            if (!db.objectStoreNames.contains("productos")) db.createObjectStore("productos", { keyPath: "id", autoIncrement: true });
            if (!db.objectStoreNames.contains("pedidos")) db.createObjectStore("pedidos", { keyPath: "id", autoIncrement: true });
        };

        request.onsuccess = (e) => {
            db = e.target.result;
            seedInitialData();
        };

        function seedInitialData() {
            const tx = db.transaction(["usuarios", "categorias", "salsas", "productos"], "readwrite");
            const storeUsers = tx.objectStore("usuarios");
            storeUsers.count().onsuccess = (e) => {
                if(e.target.result === 0) {
                    storeUsers.add({ usuario: "admin", clave: "admin", nombre: "Administrador", rol: "admin" });
                    storeUsers.add({ usuario: "mesero1", clave: "1234", nombre: "Carlos Gómez", rol: "mesero" });
                    storeUsers.add({ usuario: "multi1", clave: "1234", nombre: "Juan Multitarea", rol: "multitarea" });
                    
                    const storeCat = tx.objectStore("categorias");
                    storeCat.add({ nombre: "Alitas & Entradas" });
                    storeCat.add({ nombre: "Porciones & Acompañantes" });

                    const storeSauce = tx.objectStore("salsas");
                    storeSauce.add({ nombre: "BBQ" });
                    storeSauce.add({ nombre: "Picante" });
                    storeSauce.add({ nombre: "Sin Salsa" });

                    const storeProd = tx.objectStore("productos");
                    storeProd.add({ nombre: "Porción de Alitas (6u)", precio: 5.50, categoria: "Alitas & Entradas", requiere_salsa: true });
                    storeProd.add({ nombre: "Porción de Papas", precio: 1.50, categoria: "Porciones & Acompañantes", requiere_salsa: false });
                }
            }
        }

        let currentUser = null;
        let cart = [];
        let currentModalItem = null;

        function handleLogin(e) {
            e.preventDefault();
            const u = document.getElementById("loginUser").value.trim();
            const p = document.getElementById("loginPass").value.trim();

            const tx = db.transaction("usuarios", "readonly");
            const req = tx.objectStore("usuarios").get(u);

            req.onsuccess = () => {
                const user = req.result;
                if(user && user.clave === p) {
                    currentUser = user;
                    document.getElementById("loginScreen").classList.add("hidden");
                    document.getElementById("appScreen").classList.remove("hidden");
                    document.getElementById("userInfo").classList.remove("hidden");
                    document.getElementById("userBadge").innerText = `${user.nombre} (${user.rol.toUpperCase()})`;
                    setupNavigation();
                } else {
                    alert("Usuario o contraseña incorrectos");
                }
            };
        }

        function logout() {
            currentUser = null;
            cart = [];
            document.getElementById("appScreen").classList.add("hidden");
            document.getElementById("userInfo").classList.add("hidden");
            document.getElementById("loginScreen").classList.remove("hidden");
        }

        // ACCESOS DINÁMICOS POR ROL (MULTITAREA TIENE ACCESO A LISTA Y REPORTES)
        function setupNavigation() {
            const nav = document.getElementById("sidebar");
            nav.innerHTML = "";

            const views = {
                "mesero": [{ id: "Pedido", name: "📝 Tomar Pedido" }],
                "cocina": [{ id: "Cocina", name: "🔥 Cocina" }],
                "caja": [{ id: "Caja", name: "💰 Caja y Cobros" }],
                "multitarea": [
                    { id: "Pedido", name: "📝 Tomar Pedido" },
                    { id: "Caja", name: "💰 Caja y Cobros" },
                    { id: "Cocina", name: "🔥 Cocina" },
                    { id: "Reportes", name: "📋 Lista de Ventas" }
                ],
                "admin": [
                    { id: "Pedido", name: "📝 Tomar Pedido" },
                    { id: "Caja", name: "💰 Caja y Cobros" },
                    { id: "Cocina", name: "🔥 Cocina" },
                    { id: "Reportes", name: "📊 Reportes & Facturas" },
                    { id: "Admin", name: "⚙️ Configuración" }
                ]
            };

            const allowed = views[currentUser.rol] || views["mesero"];
            allowed.forEach((v, index) => {
                const btn = document.createElement("button");
                btn.className = "w-full text-left p-3 rounded-lg font-bold bg-slate-700 hover:bg-slate-600 transition mb-1 text-sm";
                btn.innerText = v.name;
                btn.onclick = () => switchView(v.id);
                nav.appendChild(btn);
                if (index === 0) switchView(v.id);
            });
        }

        function switchView(viewId) {
            ["Pedido", "Caja", "Cocina", "Reportes", "Admin"].forEach(v => {
                document.getElementById(`view${v}`).classList.add("hidden");
            });
            document.getElementById(`view${viewId}`).classList.remove("hidden");

            if (viewId === "Pedido") renderCatalog();
            if (viewId === "Caja") renderCaja();
            if (viewId === "Cocina") renderCocina();
            if (viewId === "Reportes") renderReports();
            if (viewId === "Admin") renderAdminConfig();
        }

        function renderCatalog() {
            const catSelect = document.getElementById("filterCategory");
            const catalogGrid = document.getElementById("catalogGrid");

            const txCat = db.transaction("categorias", "readonly");
            txCat.objectStore("categorias").getAll().onsuccess = (e) => {
                const cats = e.target.result;
                const currentVal = catSelect.value;
                catSelect.innerHTML = `<option value="Todas">Todas</option>` + cats.map(c => `<option value="${c.nombre}">${c.nombre}</option>`).join("");
                if(currentVal) catSelect.value = currentVal;
            };

            const txProd = db.transaction("productos", "readonly");
            txProd.objectStore("productos").getAll().onsuccess = (e) => {
                let prods = e.target.result;
                if(catSelect.value && catSelect.value !== "Todas") {
                    prods = prods.filter(p => p.categoria === catSelect.value);
                }
                catalogGrid.innerHTML = prods.map(p => `
                    <div class="card p-4 flex flex-col justify-between text-center">
                        <div class="font-bold mb-1">${p.nombre}</div>
                        <div class="text-emerald-400 font-bold mb-3">$${p.precio.toFixed(2)}</div>
                        <button onclick="handleAddToCart(${p.id}, '${p.nombre}', ${p.precio}, ${p.requiere_salsa})" class="btn-primary py-1.5 px-3 rounded text-xs">Agregar +</button>
                    </div>
                `).join("");
            };
        }

        function handleAddToCart(id, nombre, precio, requiereSalsa) {
            if (requiereSalsa) {
                currentModalItem = { id, nombre, precio };
                document.getElementById("modalTitle").innerText = `Opciones para: ${nombre}`;
                
                const tx = db.transaction("salsas", "readonly");
                tx.objectStore("salsas").getAll().onsuccess = (e) => {
                    const salsas = e.target.result;
                    document.getElementById("modalSauceSelect").innerHTML = salsas.map(s => `<option value="${s.nombre}">${s.nombre}</option>`).join("");
                    document.getElementById("sauceModal").classList.remove("hidden");
                };
            } else {
                cart.push({ nombre, precio });
                renderCart();
            }
        }

        function closeSauceModal() {
            document.getElementById("sauceModal").classList.add("hidden");
        }

        function confirmSauceModal() {
            const sauce = document.getElementById("modalSauceSelect").value;
            const note = document.getElementById("modalNoteInput").value.trim();
            let name = `${currentModalItem.nombre} [${sauce}]`;
            if (note) name += ` (${note})`;
            
            cart.push({ nombre: name, precio: currentModalItem.precio });
            document.getElementById("modalNoteInput").value = "";
            closeSauceModal();
            renderCart();
        }

        function addCustomItem() {
            const desc = document.getElementById("customItemDesc").value.trim();
            const price = parseFloat(document.getElementById("customItemPrice").value);
            if (desc && !isNaN(price) && price > 0) {
                cart.push({ nombre: `⭐ ${desc}`, precio: price });
                document.getElementById("customItemDesc").value = "";
                document.getElementById("customItemPrice").value = "";
                renderCart();
            }
        }

        function renderCart() {
            const container = document.getElementById("cartItems");
            let total = 0;
            container.innerHTML = cart.map((item, idx) => {
                total += item.precio;
                return `
                    <div class="flex justify-between items-center bg-slate-900 p-2 rounded text-xs">
                        <span class="font-medium">${item.nombre}</span>
                        <div class="flex items-center gap-2">
                            <span class="text-emerald-400 font-bold">$${item.precio.toFixed(2)}</span>
                            <button onclick="cart.splice(${idx}, 1); renderCart();" class="text-red-400 hover:text-red-300 font-bold">✕</button>
                        </div>
                    </div>
                `;
            }).join("");
            document.getElementById("cartTotal").innerText = `$${total.toFixed(2)}`;
        }

        function submitOrder() {
            const client = document.getElementById("orderClient").value.trim();
            if (!client) return alert("Ingresa el nombre del cliente o mesa.");
            if (cart.length === 0) return alert("El carrito está vacío.");

            const ruc = document.getElementById("factRuc").value.trim();
            const razon = document.getElementById("factRazon").value.trim();
            const phone = document.getElementById("factPhone").value.trim();
            const email = document.getElementById("factEmail").value.trim();

            const total = cart.reduce((acc, i) => acc + i.precio, 0);
            const now = new Date().toISOString().replace('T', ' ').substring(0, 19);

            const tx = db.transaction("pedidos", "readwrite");
            tx.objectStore("pedidos").add({
                cliente: client,
                fact_ruc: ruc || "Consumidor Final",
                fact_razon: razon || client,
                fact_phone: phone,
                fact_email: email,
                items: JSON.stringify(cart),
                total: total,
                estado: "pendiente",
                mesero: currentUser.nombre,
                metodo_pago: "Efectivo",
                fecha_hora: now
            });

            tx.oncomplete = () => {
                cart = [];
                document.getElementById("orderClient").value = "";
                document.getElementById("factRuc").value = "";
                document.getElementById("factRazon").value = "";
                document.getElementById("factPhone").value = "";
                document.getElementById("factEmail").value = "";
                renderCart();
                alert("¡Pedido y Datos de Factura registrados con éxito!");
            };
        }

        function renderCaja() {
            const container = document.getElementById("pendingOrders");
            const tx = db.transaction("pedidos", "readonly");
            tx.objectStore("pedidos").getAll().onsuccess = (e) => {
                const pending = e.target.result.filter(p => p.estado !== "cobrado" && p.estado !== "anulado");
                container.innerHTML = pending.map(p => `
                    <div class="card p-4 space-y-3">
                        <div class="flex justify-between items-center">
                            <span class="font-bold text-sky-400">Orden #${p.id} - ${p.cliente}</span>
                            <span class="text-xs text-slate-400">Mesero: ${p.mesero}</span>
                        </div>
                        <div class="text-xs text-slate-400 bg-slate-900 p-2 rounded">
                            <div>RUC/CI: <span class="text-white">${p.fact_ruc || 'N/A'}</span></div>
                            <div>Razón Social: <span class="text-white">${p.fact_razon || 'N/A'}</span></div>
                        </div>
                        <div class="text-2xl font-bold text-emerald-400">$${p.total.toFixed(2)}</div>
                        <select id="payMethod_${p.id}" class="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm text-white">
                            <option value="Efectivo">Efectivo</option>
                            <option value="Transf. Banco de Loja">Transf. Banco de Loja</option>
                            <option value="Transf. Banco Pichincha">Transf. Banco Pichincha</option>
                        </select>
                        <button onclick="processPayment(${p.id})" class="w-full btn-primary py-2 rounded text-sm">💵 COBRAR</button>
                    </div>
                `).join("");
            };
        }

        function processPayment(orderId) {
            const method = document.getElementById(`payMethod_${orderId}`).value;
            const tx = db.transaction("pedidos", "readwrite");
            const store = tx.objectStore("pedidos");
            store.get(orderId).onsuccess = (e) => {
                const order = e.target.result;
                order.estado = "cobrado";
                order.metodo_pago = method;
                store.put(order);
                tx.oncomplete = () => renderCaja();
            };
        }

        function renderCocina() {
            const container = document.getElementById("kitchenOrders");
            const tx = db.transaction("pedidos", "readonly");
            tx.objectStore("pedidos").getAll().onsuccess = (e) => {
                const pending = e.target.result.filter(p => p.estado === "pendiente");
                container.innerHTML = pending.map(p => {
                    const items = JSON.parse(p.items);
                    return `
                        <div class="card p-4 border-orange-500 space-y-3">
                            <div class="font-bold text-orange-400">Orden #${p.id} - ${p.cliente}</div>
                            <ul class="text-sm space-y-1 bg-slate-900 p-2 rounded">
                                ${items.map(i => `<li>• ${i.nombre}</li>`).join("")}
                            </ul>
                            <button onclick="markKitchenReady(${p.id})" class="w-full bg-orange-500 hover:bg-orange-600 font-bold py-2 rounded text-sm">✔ MARCAR LISTO</button>
                        </div>
                    `;
                }).join("");
            };
        }

        function markKitchenReady(orderId) {
            const tx = db.transaction("pedidos", "readwrite");
            const store = tx.objectStore("pedidos");
            store.get(orderId).onsuccess = (e) => {
                const order = e.target.result;
                order.estado = "preparado";
                store.put(order);
                tx.oncomplete = () => renderCocina();
            };
        }

        function renderReports() {
            const dateVal = document.getElementById("reportDate").value || new Date().toISOString().substring(0, 10);
            document.getElementById("reportDate").value = dateVal;

            const tx = db.transaction("pedidos", "readonly");
            tx.objectStore("pedidos").getAll().onsuccess = (e) => {
                const all = e.target.result.filter(p => p.fecha_hora.startsWith(dateVal));
                const cobrados = all.filter(p => p.estado === "cobrado");
                
                const totalMonto = cobrados.reduce((acc, p) => acc + p.total, 0);
                document.getElementById("kpiTotal").innerText = `$${totalMonto.toFixed(2)}`;
                document.getElementById("kpiCount").innerText = all.length;

                const breakdown = {};
                cobrados.forEach(p => {
                    breakdown[p.metodo_pago] = (breakdown[p.metodo_pago] || 0) + p.total;
                });

                document.getElementById("paymentBreakdown").innerHTML = Object.keys(breakdown).map(m => `
                    <div class="bg-slate-900 p-3 rounded text-center">
                        <div class="text-xs text-sky-400 font-bold">${m}</div>
                        <div class="text-lg font-bold text-emerald-400">$${breakdown[m].toFixed(2)}</div>
                    </div>
                `).join("") || `<div class="text-xs text-slate-500">Sin ventas hoy.</div>`;

                document.getElementById("reportTableBody").innerHTML = all.map(p => `
                    <tr>
                        <td class="p-2">#${p.id}</td>
                        <td class="p-2">${p.fecha_hora}</td>
                        <td class="p-2">${p.mesero}</td>
                        <td class="p-2">${p.fact_razon || p.cliente}</td>
                        <td class="p-2 text-slate-400">${p.fact_ruc || 'N/A'}</td>
                        <td class="p-2 text-sky-400">${p.metodo_pago}</td>
                        <td class="p-2 text-emerald-400 font-bold">$${p.total.toFixed(2)}</td>
                        <td class="p-2 font-bold ${p.estado === 'cobrado' ? 'text-emerald-400' : 'text-sky-400'}">${p.estado.toUpperCase()}</td>
                    </tr>
                `).join("");
            };
        }

        // FUNCIÓN GENERAR Y DESCARGAR PDF PARA LA CONTADORA
        function exportContadoraPDF() {
            const { jsPDF } = window.jspdf;
            const doc = new jsPDF();
            const dateVal = document.getElementById("reportDate").value || new Date().toISOString().substring(0, 10);

            const tx = db.transaction("pedidos", "readonly");
            tx.objectStore("pedidos").getAll().onsuccess = (e) => {
                const all = e.target.result.filter(p => p.fecha_hora.startsWith(dateVal) && p.estado === "cobrado");

                // Encabezado
                doc.setFontSize(18);
                doc.setTextColor(16, 185, 129);
                doc.text("FastFood POS Pro - Reporte Fiscal de Ventas", 14, 15);
                
                doc.setFontSize(10);
                doc.setTextColor(100);
                doc.text(`Fecha del Reporte: ${dateVal}`, 14, 22);
                doc.text(`Generado por: ${currentUser.nombre} (${currentUser.rol.toUpperCase()})`, 14, 27);

                const totalVentas = all.reduce((acc, p) => acc + p.total, 0);
                const subtotalBase = totalVentas / 1.15; // Estimación base
                const ivaMonto = totalVentas - subtotalBase;

                // Cuadro Resumen Financiero
                doc.autoTable({
                    startY: 32,
                    head: [['Métrica Fiscal', 'Valor USD ($)']],
                    body: [
                        ['Total Transacciones Cobradas', `${all.length}`],
                        ['Subtotal Neto Estimado', `$${subtotalBase.toFixed(2)}`],
                        ['IVA Estimado (15%)', `$${ivaMonto.toFixed(2)}`],
                        ['TOTAL RECAUDADO', `$${totalVentas.toFixed(2)}`]
                    ],
                    theme: 'grid',
                    headStyles: { fillColor: [30, 41, 59] }
                });

                // Tabla Detallada para Contabilidad
                const tableData = all.map(p => [
                    `#${p.id}`,
                    p.fecha_hora.substring(11, 19),
                    p.fact_ruc || 'Consumidor Final',
                    p.fact_razon || p.cliente,
                    p.metodo_pago,
                    `$${p.total.toFixed(2)}`
                ]);

                doc.autoTable({
                    startY: doc.lastAutoTable.finalY + 10,
                    head: [['ID', 'Hora', 'RUC / Cédula', 'Razón Social / Cliente', 'Forma Pago', 'Total']],
                    body: tableData,
                    theme: 'striped',
                    headStyles: { fillColor: [16, 185, 129] }
                });

                doc.save(`Reporte_Contadora_FastFood_${dateVal}.pdf`);
            };
        }

        function renderAdminConfig() {
            renderUsers();
            const txCat = db.transaction("categorias", "readonly");
            txCat.objectStore("categorias").getAll().onsuccess = (e) => {
                document.getElementById("catList").innerHTML = e.target.result.map(c => `
                    <li class="py-2 flex justify-between items-center">
                        <span>${c.nombre}</span>
                        <button onclick="deleteCategory(${c.id})" class="text-red-400 text-xs font-bold">Eliminar</button>
                    </li>
                `).join("");
            };

            const txSauce = db.transaction("salsas", "readonly");
            txSauce.objectStore("salsas").getAll().onsuccess = (e) => {
                document.getElementById("sauceList").innerHTML = e.target.result.map(s => `
                    <li class="py-2 flex justify-between items-center">
                        <span>${s.nombre}</span>
                        <button onclick="deleteSauce(${s.id})" class="text-red-400 text-xs font-bold">Eliminar</button>
                    </li>
                `).join("");
            };
        }

        function renderUsers() {
            const tx = db.transaction("usuarios", "readonly");
            tx.objectStore("usuarios").getAll().onsuccess = (e) => {
                const users = e.target.result;
                document.getElementById("usersTableBody").innerHTML = users.map(u => `
                    <tr>
                        <td class="p-2 font-medium">${u.nombre}</td>
                        <td class="p-2 text-slate-400">${u.usuario}</td>
                        <td class="p-2"><span class="bg-slate-700 px-2 py-1 rounded text-xs font-bold uppercase">${u.rol}</span></td>
                        <td class="p-2">
                            ${u.usuario !== currentUser.usuario ? `<button onclick="deleteUser('${u.usuario}')" class="text-red-400 hover:text-red-300 font-bold text-xs">Eliminar</button>` : '<span class="text-xs text-slate-500">Actual</span>'}
                        </td>
                    </tr>
                `).join("");
            };
        }

        function addUser() {
            const nombre = document.getElementById("newFullName").value.trim();
            const usuario = document.getElementById("newUsername").value.trim();
            const clave = document.getElementById("newPassword").value.trim();
            const rol = document.getElementById("newRole").value;

            if (!nombre || !usuario || !clave) return alert("Completa todos los campos para crear el usuario.");

            const tx = db.transaction("usuarios", "readwrite");
            const store = tx.objectStore("usuarios");
            
            store.get(usuario).onsuccess = (e) => {
                if(e.target.result) {
                    alert("El nombre de usuario ya existe.");
                } else {
                    store.add({ usuario, clave, nombre, rol });
                    tx.oncomplete = () => {
                        document.getElementById("newFullName").value = "";
                        document.getElementById("newUsername").value = "";
                        document.getElementById("newPassword").value = "";
                        renderUsers();
                        alert("Usuario registrado con éxito.");
                    };
                }
            };
        }

        function deleteUser(username) {
            if(confirm(`¿Seguro que deseas eliminar al usuario '${username}'?`)) {
                const tx = db.transaction("usuarios", "readwrite");
                tx.objectStore("usuarios").delete(username);
                tx.oncomplete = () => renderUsers();
            }
        }

        function addCategory() {
            const name = document.getElementById("newCatName").value.trim();
            if (name) {
                const tx = db.transaction("categorias", "readwrite");
                tx.objectStore("categorias").add({ nombre: name });
                tx.oncomplete = () => {
                    document.getElementById("newCatName").value = "";
                    renderAdminConfig();
                };
            }
        }

        function deleteCategory(id) {
            const tx = db.transaction("categorias", "readwrite");
            tx.objectStore("categorias").delete(id);
            tx.oncomplete = () => renderAdminConfig();
        }

        function addSauce() {
            const name = document.getElementById("newSauceName").value.trim();
            if (name) {
                const tx = db.transaction("salsas", "readwrite");
                tx.objectStore("salsas").add({ nombre: name });
                tx.oncomplete = () => {
                    document.getElementById("newSauceName").value = "";
                    renderAdminConfig();
                };
            }
        }

        function deleteSauce(id) {
            const tx = db.transaction("salsas", "readwrite");
            tx.objectStore("salsas").delete(id);
            tx.oncomplete = () => renderAdminConfig();
        }
    </script>
</body>
</html>
