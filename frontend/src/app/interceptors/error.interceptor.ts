import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { MessageService } from 'primeng/api';
import { catchError, throwError } from 'rxjs';

export const errorInterceptor: HttpInterceptorFn = (req, next) => {
    const messageService = inject(MessageService);

    return next(req).pipe(
        catchError((error: HttpErrorResponse) => {
            let errorMessage = 'Ein unbekannter Fehler ist aufgetreten.';
            let errorSummary = 'Fehler';

            if (error.error instanceof ErrorEvent) {
                // Client-side error
                errorMessage = error.error.message;
                errorSummary = 'Client-Fehler';
            } else {
                // Server-side error
                switch (error.status) {
                    case 0:
                        errorMessage = 'Verbindung zum Server fehlgeschlagen. Bitte prüfen, ob das Backend läuft.';
                        errorSummary = 'Verbindungsfehler';
                        break;
                    case 400:
                        errorSummary = 'Ungültige Anfrage';
                        errorMessage = error.error?.detail || error.message;
                        break;
                    case 404:
                        errorSummary = 'Nicht gefunden';
                        errorMessage = 'Die angeforderte Ressource wurde nicht gefunden.';
                        break;
                    case 422:
                        errorSummary = 'Validierungsfehler';
                        if (error.error?.detail && Array.isArray(error.error.detail)) {
                            // Format Pydantic validation errors
                            errorMessage = error.error.detail.map((e: any) => `${e.loc.join('.')}: ${e.msg}`).join('\n');
                        } else {
                            errorMessage = error.error?.detail || error.message;
                        }
                        break;
                    case 500:
                        errorSummary = 'Server-Fehler';
                        errorMessage = 'Ein interner Serverfehler ist aufgetreten.';
                        break;
                    default:
                        errorMessage = `Fehler Code ${error.status}: ${error.error?.detail || error.message}`;
                        break;
                }
            }

            messageService.add({
                severity: 'error',
                summary: errorSummary,
                detail: errorMessage,
                life: 5000
            });

            return throwError(() => error);
        })
    );
};
