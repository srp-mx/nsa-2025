import { Component } from '@angular/core';

import * as L from 'leaflet';
import 'leaflet-routing-machine';
import { icon, Marker } from 'leaflet';
import { Inject, Input, OnInit } from '@angular/core';
import 'leaflet.heat';
import { MapService } from '../_service/map/map.service';
import { Subscription } from 'rxjs';
import { MapResponse } from '../_model/map'
import { HttpErrorResponse, HttpResponse } from '@angular/common/http';

export const DEFAULT_LAT = 34.0522;
export const DEFAULT_LON =  -118.2437;
export const TITULO = 'Proyecto';

const iconRetinaUrl = 'assets/marker-icon-2x.png';
const iconUrl = 'assets/marker-icon.png';
const shadowUrl = 'assets/marker-shadow.png';

@Component({
  selector: 'app-map',
  imports: [],
  templateUrl: './map.component.html',
  styleUrl: './map.component.css'
})

export class MapComponent implements OnInit {

  private map:any;

  @Input() lat: number = DEFAULT_LAT;
  @Input() lon: number = DEFAULT_LON;
  @Input() titulo: string = TITULO ;

  private subscriptions: Subscription[] = [];

  constructor(private mapService: MapService) {}

  ngOnInit(): void {
    this.initMap();
  }

  private initMap(): void {
    this.map = L.map('map').setView([this.lat, this.lon], 10);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 18,
    }).addTo(this.map);
    this.subscriptions.push(
      this.mapService.getCurrentMap(this.lat, this.lon).subscribe({
        next: (res: MapResponse) => {
          const map_data = this.mapService.processMapData(res);

          console.log(map_data);

          for (var contaminante in map_data) {
            var heatPoints: number[][] = map_data[contaminante];

            var heat = (L as any).heatLayer(heatPoints, {maxZoom: 10, blur: 70}).addTo(this.map);
          }
        },
        error: (err: HttpErrorResponse) => {
          console.error('Error fetching map data', err);
        }
      })
    );
  }

  ngOnDestroy(): void {
    this.subscriptions.forEach(sub => sub.unsubscribe());
  }
}