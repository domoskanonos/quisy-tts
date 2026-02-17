import { Routes } from '@angular/router';

export const routes: Routes = [
    {
        path: '',
        redirectTo: 'synthesis',
        pathMatch: 'full',
    },
    {
        path: 'synthesis',
        loadComponent: () =>
            import('./pages/synthesis/synthesis.component').then(m => m.SynthesisComponent),
    },
    {
        path: 'voices',
        loadComponent: () =>
            import('./pages/voices/voices.component').then(m => m.VoicesComponent),
    },
    {
        path: 'status',
        loadComponent: () =>
            import('./pages/status/status.component').then(m => m.StatusComponent),
    },
];
