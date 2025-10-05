import { Component } from '@angular/core';
import { FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
//import { AuthenticationService } from '../../_service/authentication.service';
import { Subscription } from 'rxjs';
import { Router, RouterModule } from '@angular/router';
//import { User } from '../../_model/user';
import { HttpErrorResponse } from '@angular/common/http';
import { CommonModule } from '@angular/common';
import { SwalMessages } from '../../shared/swal-messages';

import { FontAwesomeModule, FaIconLibrary } from '@fortawesome/angular-fontawesome';
import { fas } from '@fortawesome/free-solid-svg-icons';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [ReactiveFormsModule, CommonModule, RouterModule, FontAwesomeModule],
  templateUrl: './register.component.html',
  styleUrl: './register.component.css'
})
export class RegisterComponent {

  swal: SwalMessages = new SwalMessages(); // swal messages

  registerForm = new FormGroup(
    {
     mail: new FormControl('', [Validators.required]),
     name: new FormControl('', [Validators.required]),
     password: new FormControl('', [Validators.required]),
     surname: new FormControl('', [Validators.required]),
     username: new FormControl('', [Validators.required])
    },    
  );

  private subscriptions: Subscription[] = [];

  constructor(private router: Router, library: FaIconLibrary) {
    library.addIconPacks(fas);
  }

  ngOnInit(): void {
    //if (this.authenticationService.isUserLoggedIn()) {
      //this.router.navigateByUrl('');

  }

  public onRegister(): void {
    /** 
    var usuarioFormValue  = this.registerForm.value as User;
    var usuario: User = new User();

    usuario.mail = usuarioFormValue.mail;
    usuario.name = usuarioFormValue.name;
    usuario.surname = usuarioFormValue.surname;
    usuario.password = usuarioFormValue.password;
    usuario.rfc = usuarioFormValue.rfc;
    usuario.username = usuarioFormValue.username;

    this.subscriptions.push(
      this.authenticationService.register(usuario).subscribe(
        (response: {message: string}) => {
          this.swal.successMessage("¡Tu cuenta ha sido creada exitosamente!");
        },
        (errorResponse: HttpErrorResponse) => {
          this.swal.errorMessage(errorResponse.error.message);
        }
      )
    );*/
  }
  ngOnDestroy(): void {
    this.subscriptions.forEach(sub => sub.unsubscribe());
  }

  get fg() {
    return this.registerForm.controls;
  }

}