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

  @Input() lat: number = 34;
  @Input() lon: number = -118;
  @Input() titulo: string = TITULO ;

  public fechaInicio: String | null = null;
  public fechaFin: String | null = null;
  private itemlat: String | null = null;
  private itemlon: String | null = null;

  private subscriptions: Subscription[] = [];

  constructor(private mapService: MapService) {}

  ngOnInit(): void {
    this.initMap();
    this.setupTimePeriodSelector();
    this.setupSearchAutocomplete();
  }

  private updateMapData(lat: number, lon: number): void {
    // Eliminamos capas anteriores (si existen)
    this.map.eachLayer((layer: any) => {
      if (layer instanceof L.TileLayer) return; // mantenemos solo el fondo
      this.map.removeLayer(layer);
    });

    // Hacemos la nueva petición al servicio con las coordenadas actualizadas
    this.subscriptions.push(
      this.mapService.getCurrentMap(lat, lon).subscribe({
        next: (res: MapResponse) => {
          const map_data = this.mapService.processMapData(res);
          console.log('New map data for coords:', lat, lon, map_data);

          for (const contaminante in map_data) {
            const heatPoints: number[][] = map_data[contaminante];
            const heat = (L as any).heatLayer(heatPoints, {
              max: res.products[contaminante].max_value,
              gradient: {
                0.000: '#440154',
                0.100: '#482173',
                0.200: '#433E85',
                0.300: '#38598C',
                0.400: '#2D708E',
                0.500: '#25858E',
                0.600: '#1E9B8A',
                0.700: '#2BB07F',
                0.800: '#51C56A',
                0.900: '#85D54A',
                1.000: '#FDE725'
              }
            }).addTo(this.map);
          }
        },
        error: (err: HttpErrorResponse) => {
          console.error('Error fetching map data', err);
        }
      })
    );
  }


  private initMap(): void {
    this.map = L.map('map').setView([this.lat, this.lon], 10);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 18,
    }).addTo(this.map);

    this.updateMapData(this.lat, this.lon);    
  }

  ngOnDestroy(): void {
    this.subscriptions.forEach(sub => sub.unsubscribe());
  }

  /**
   * Configura el 'change' listener para el selector de tipo de límite.
   */
  private setupTimePeriodSelector(): void {
    const selector = document.getElementById('time-limit-type') as HTMLSelectElement;

    if (selector) {
      selector.addEventListener('change', () => this.handleTimeLimitTypeChange(selector.value));
      document.getElementById('start-date')?.addEventListener('change', () => this.updateDateRange());
      document.getElementById('end-date')?.addEventListener('change', () => this.updateDateRange());
      document.getElementById('start-time')?.addEventListener('change', () => this.updateTimeRange());
      document.getElementById('end-time')?.addEventListener('change', () => this.updateTimeRange());
    }
  }

  private setupSearchAutocomplete(): void {
    const searchInput = document.getElementById('place-search') as HTMLInputElement;
    const suggestionsContainer = document.getElementById('suggestions-container') as HTMLDivElement;

    if (!searchInput || !suggestionsContainer) return;

    // Usamos un pequeño retardo (debounce) para no saturar el servidor con peticiones
    let debounceTimer: any;

    searchInput.addEventListener('input', () => {
      clearTimeout(debounceTimer);

      const query = searchInput.value.trim();

      if (query.length < 3) {
        suggestionsContainer.innerHTML = '';
        suggestionsContainer.style.display = 'none';
        return;
      }

      debounceTimer = setTimeout(() => {
        this.fetchSuggestions(query, suggestionsContainer, searchInput);
      }, 300); // Espera 300ms antes de buscar
    });

    // Ocultar sugerencias si el usuario hace clic fuera del input
    document.addEventListener('click', (event) => {
      if (!searchInput.contains(event.target as Node) && !suggestionsContainer.contains(event.target as Node)) {
        suggestionsContainer.style.display = 'none';
      }
    });
  }

  /**
   * Realiza la petición a Nominatim y muestra las sugerencias.
   * @param query El texto de búsqueda.
   * @param container El contenedor DOM para las sugerencias.
   * @param input El input de búsqueda.
   */
  private fetchSuggestions(query: string, container: HTMLDivElement, input: HTMLInputElement): void {
    // URL de Nominatim para geocodificación (autocompletado)
    const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=5`;

    fetch(url)
      .then(response => response.json())
      .then((data: any[]) => {
        container.innerHTML = '';
        if (data.length > 0) {
          data.forEach(item => {
            const suggestionItem = document.createElement('div');
            suggestionItem.classList.add('suggestion-item');
            suggestionItem.textContent = item.display_name;
            suggestionItem.addEventListener('click', () => {
              input.value = item.display_name;
              container.innerHTML = '';
              container.style.display = 'none';
              parseFloat(item.lat);
              parseFloat(item.lon);
              this.itemlat = String(item.lat);
              this.itemlon = String(item.lon);
              this.lat = item.lat;
              this.lon = item.lon; 
              
              this.updateMapData(this.lat, this.lon);  
              this.map.setView([parseFloat(item.lat), parseFloat(item.lon)], 16);
              //L.marker([parseFloat(item.lat), parseFloat(item.lon)]).addTo(this.map);
            });
            container.appendChild(suggestionItem);
          });
          container.style.display = 'block';
        } else {
          container.style.display = 'none';
        }
      })
      .catch(error => console.error('Error fetching geocoding data:', error));
  }

  /**
   * Muestra u oculta los inputs relevantes y resetea las variables de fecha.
   * @param value El valor seleccionado en el dropdown ('none', 'date', 'time').
   */
  private handleTimeLimitTypeChange(value: string): void {
    const dateInputs = document.getElementById('date-inputs');
    const timeInputs = document.getElementById('time-inputs');

    this.fechaInicio = null;
    this.fechaFin = null;

    if (dateInputs && timeInputs) {
      dateInputs.classList.add('hidden');
      timeInputs.classList.add('hidden');

      if (value === 'date') {
        dateInputs.classList.remove('hidden');
        this.updateDateRange();
      } else if (value === 'time') {
        timeInputs.classList.remove('hidden');
        this.updateTimeRange();
      }

      console.log('Fecha Inicio:', this.fechaInicio);
      console.log('Fecha Fin:', this.fechaFin);
    }
  }

  /**
   * Actualiza las variables fechaInicio y fechaFin con el intervalo de fechas seleccionado.
   */
  private updateDateRange(): void {
    const startDateInput = document.getElementById('start-date') as HTMLInputElement;
    const endDateInput = document.getElementById('end-date') as HTMLInputElement;

    if (startDateInput.value) {
      // Si se selecciona un intervalo, se guarda la fecha seleccionada.
      this.fechaInicio = String(new Date(startDateInput.value));
    }
    if (endDateInput.value) {
      // Se ajusta la fecha fin para ser al final del día seleccionado para incluir todo el día.
      const endDate = new Date(endDateInput.value);
      endDate.setHours(23, 59, 59, 999);
      this.fechaFin = String(endDate);
    }
  }

  /**
   * Actualiza las variables fechaInicio y fechaFin con la hora seleccionada del día de hoy.
   */
  private updateTimeRange(): void {
    const startTimeInput = document.getElementById('start-time') as HTMLInputElement;
    const endTimeInput = document.getElementById('end-time') as HTMLInputElement;

    const today = new Date();
    today.setHours(0, 0, 0, 0); 

    // Si se selecciona una hora, se da con el día de hoy.
    if (startTimeInput.value) {
      const [hours, minutes] = startTimeInput.value.split(':').map(Number);
      const startDateTime = new Date(today);
      startDateTime.setHours(hours, minutes);
      this.fechaInicio = String(startDateTime);
    }

    if (endTimeInput.value) {
      const [hours, minutes] = endTimeInput.value.split(':').map(Number);
      const endDateTime = new Date(today);
      endDateTime.setHours(hours, minutes);
      this.fechaFin = String(endDateTime);
    }
  }
}