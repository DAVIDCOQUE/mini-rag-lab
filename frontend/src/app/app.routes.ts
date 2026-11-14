import { Routes } from '@angular/router';

import { MainLayoutComponent } from './layout/main-layout.component';
import { maintainerGuard } from './core/auth/maintainer.guard';

export const routes: Routes = [
  {
    path: 'login',
    loadComponent: () =>
      import('./features/login/login.component').then((m) => m.LoginComponent),
  },
  {
    path: '',
    component: MainLayoutComponent,
    children: [
      { path: '', redirectTo: 'home', pathMatch: 'full' },
      {
        path: 'home',
        loadComponent: () =>
          import('./features/home/home.component').then((m) => m.HomeComponent),
      },
      {
        path: 'chat',
        loadComponent: () =>
          import('./features/chat/chat.component').then((m) => m.ChatComponent),
      },
      {
        path: 'documents',
        canActivate: [maintainerGuard],
        loadComponent: () =>
          import('./features/documents/documents.component').then((m) => m.DocumentsComponent),
      },
      {
        path: 'search',
        canActivate: [maintainerGuard],
        loadComponent: () =>
          import('./features/search/search.component').then((m) => m.SearchComponent),
      },
      {
        path: 'prompts',
        canActivate: [maintainerGuard],
        loadComponent: () =>
          import('./features/prompts/prompts.component').then((m) => m.PromptsComponent),
      },
      {
        path: 'conversations',
        canActivate: [maintainerGuard],
        loadComponent: () =>
          import('./features/conversations/conversations.component').then(
            (m) => m.ConversationsComponent,
          ),
      },
      {
        path: 'profile',
        canActivate: [maintainerGuard],
        loadComponent: () =>
          import('./features/profile/profile.component').then((m) => m.ProfileComponent),
      },
    ],
  },
  { path: '**', redirectTo: '' },
];
