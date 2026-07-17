export const environment = {
  production: false,
  // Vacio = rutas relativas servidas por el proxy de Angular (proxy.conf.json) hacia FastAPI.
  // Evita problemas de CORS en desarrollo al quedar todo en el mismo origen.
  apiUrl: '',
};
