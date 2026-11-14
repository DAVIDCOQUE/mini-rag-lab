import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { MaintainerAuthService } from '../services/maintainer-auth.service';

export const maintainerGuard: CanActivateFn = (_route, state) => {
  const auth = inject(MaintainerAuthService);
  const router = inject(Router);

  return auth.isAuthenticated()
    ? true
    : router.createUrlTree(['/login'], { queryParams: { returnUrl: state.url } });
};
