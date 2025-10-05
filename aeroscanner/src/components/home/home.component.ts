import { Component } from '@angular/core';
import { Router, RouterModule } from '@angular/router';
import { FontAwesomeModule, FaIconLibrary } from '@fortawesome/angular-fontawesome';
import { fas } from '@fortawesome/free-solid-svg-icons';

@Component({
  selector: 'app-home',
  imports: [],
  templateUrl: './home.component.html',
  styleUrl: './home.component.css'
})
export class HomeComponent {
  constructor(private router: Router, library: FaIconLibrary) {
      library.addIconPacks(fas);
  }

  public onSubmit(): void {
    this.router.navigateByUrl('/login');
  }
}
