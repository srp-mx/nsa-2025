import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

import { FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { FontAwesomeModule, FaIconLibrary } from '@fortawesome/angular-fontawesome';
import { fas } from '@fortawesome/free-solid-svg-icons';
import { Subscription } from 'rxjs';
import { HttpErrorResponse, HttpResponse } from '@angular/common/http';
import { AuthenticationService } from '../_service/auth/authentication.service';
import { LoginResponse } from '../_model/login-response';

@Component({
  selector: 'app-login',
  imports: [ReactiveFormsModule, CommonModule, FontAwesomeModule],
  templateUrl: './login.component.html',
  styleUrl: './login.component.css'
})
export class LoginComponent {
  
  loginForm = new FormGroup(
    {
      mail: new FormControl('', [Validators.required, Validators.email]),
      password: new FormControl('', [Validators.required, Validators.minLength(8)])
    }
  )

  private subscriptions: Subscription[] = [];

  constructor(private router: Router, library: FaIconLibrary, private authenticationService: AuthenticationService) {
    library.addIconPacks(fas);
  }

  public onLogin(): void {
    var loginFormValue = this.loginForm.value as { username: string, password: string };

    this.subscriptions.push(
      this.authenticationService.login(loginFormValue).subscribe(
        (response: HttpResponse<LoginResponse>) => {
          if (response.body && response.body.access) {
            const token = response.body.access;
            const refresh = response.body.refresh;
            this.authenticationService.saveTokens(token, refresh);
            this.router.navigateByUrl('');
          }else{
            if (response.body === null) {
              console.log('La API no devolvió cuerpo en la respuesta');
              return;
            }
            console.log('El token devuelto no fue poblado')
            return;
          }          
        },
        (errorResponse: HttpErrorResponse) => {
          alert(errorResponse.error.message);
        }
      )
    );
  }

  startTokenRefreshScheduler() {
    setInterval(() => {
      this.authenticationService.refreshToken().subscribe({
        next: (res) => {
          console.log('Token refreshed');
          this.authenticationService.saveToken(res.access);
        },
        error: (err) => {
          console.error('Error refreshing token', err);
        }
      });
    }, 60 * 60 * 1000); // cada hora
  }

  get fg() {
    return this.loginForm.controls;
  }

  ngOnDestroy(): void {
    this.subscriptions.forEach(sub => sub.unsubscribe());
  }
}
