import { ApplicationConfig, provideBrowserGlobalErrorListeners } from '@angular/core';
import { provideRouter } from '@angular/router';
// import { provideHttpClient } from '@angular/common/http';  // ← descomente ao migrar para endpoints reais
import { routes } from './app.routes';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes),
    // provideHttpClient(),  // ← descomente ao migrar para endpoints reais
  ],
};
