import { Routes } from '@angular/router';
import { LoginComponent } from '../components/login/login.component';
import { MapComponent } from '../components/map/map.component';
import { RegisterComponent } from '../components/register/register.component';

export const routes: Routes = [
    {
        path: 'login',
        component: LoginComponent
    },
    {
        path: 'map',
        component: MapComponent
    },
    {
        path: 'register',
        component: RegisterComponent
    }
];
