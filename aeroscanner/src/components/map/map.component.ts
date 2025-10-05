import { Component } from '@angular/core';

import * as L from 'leaflet';
import 'leaflet-routing-machine';
import { icon, Marker } from 'leaflet';
import { Inject, Input, OnInit } from '@angular/core';
import 'leaflet.heat';

export const DEFAULT_LAT = 48.20807;
export const DEFAULT_LON =  16.37320;
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

  constructor() {}

  ngOnInit(): void {
    this.initMap();
  }

  private initMap(): void {
    this.map = L.map('map').setView([50.5, 30.5], 17);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 18,
    }).addTo(this.map);

    // 👇 Crear un heatmap
    const heatPoints = [
      [50.5, 30.5, 1],
      [50.6, 30.4, 1],
      [50.4, 30.6, 1],
    ];

    const heat = (L as any).heatLayer(heatPoints, {
      maxZoom: 15,
      minOpacity: 0.4
    }).addTo(this.map);
  }
}