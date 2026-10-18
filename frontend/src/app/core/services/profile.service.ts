import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { AssistantProfile, AssistantProfileUpdate } from '../models/profile.model';

@Injectable({ providedIn: 'root' })
export class ProfileService {
  private readonly http = inject(HttpClient);
  private readonly endpoint = `${environment.apiUrl}/api/profile`;

  get(): Observable<AssistantProfile> {
    return this.http.get<AssistantProfile>(this.endpoint);
  }

  update(changes: AssistantProfileUpdate): Observable<AssistantProfile> {
    return this.http.put<AssistantProfile>(this.endpoint, changes);
  }
}
