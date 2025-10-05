import { Injectable } from '@angular/core';

import { HttpClient, HttpResponse } from '@angular/common/http';
import { Observable } from 'rxjs';
import { api_nsa } from '../../../shared/api-nsa';
import { User } from '../../_model/user'
import { LoginResponse } from '../../_model/login-response';

@Injectable({
  providedIn: 'root'
})
export class AuthenticationService {

  private token: string | null;  
  private refresh_token: string | null;

  constructor(private http: HttpClient) { 
    this.token = '';
    this.refresh_token = '';
  }

  public login(credenciales: {username?: string, password?: string}): Observable<HttpResponse<LoginResponse>> {
    return this.http.post<LoginResponse>(`${api_nsa}/auth/login`, credenciales, { observe: 'response' });
  }

  public refreshToken(): Observable<{access: string}> {
    if (!this.refresh_token) {
      throw new Error('No refresh token found');
    }
    return this.http.post<{access: string}>(`${api_nsa}/auth/refresh/`, this.refresh_token );
  }

  public register(user: User): Observable<{message: string}> {
    return this.http.post<{message: string}>(`${api_nsa}/auth/signup`, user);
  }

  public logout(): Observable<{message: string}> {
    return this.http.post<{message: string}>(`${api_nsa}/auth/logout`, this.refresh_token);
  }

  public saveTokens(token: string, refresh_token: string): void {
    this.token = token;
    localStorage.setItem('token', token);
    this.refresh_token = refresh_token;
  }

  public saveToken(token: string): void {
    this.token = token;
    localStorage.setItem('token', token);
  }
}
