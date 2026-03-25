import { bootstrapApplication } from '@angular/platform-browser';
import { appConfig } from './app/app.config';
import { App } from './app/app';

bootstrapApplication(App, appConfig).catch((err: unknown) => {
  // keep the handler simple and typed; `unknown` avoids implicit `any`
  // eslint-disable-next-line no-console
  console.error(err);
});
