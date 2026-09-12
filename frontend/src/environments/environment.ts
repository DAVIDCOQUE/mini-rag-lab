export const environment = {
  production: true,
  // Vacio = rutas relativas. Nginx sirve la SPA y reenvia /api y /health al backend,
  // asi que todo queda en el mismo origen y no hay CORS que resolver.
  apiUrl: '',
};
