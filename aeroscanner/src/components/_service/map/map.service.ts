import { Injectable } from '@angular/core';


import { Observable } from 'rxjs';
import { MapResponse } from '../../_model/map'

//import { of } from 'rxjs';
//import { MOCK_MAP_RESPONSE } from '../map/mock-map';
import { HttpClient, HttpParams } from '@angular/common/http';

@Injectable({
  providedIn: 'root'
})
export class MapService {

  constructor(private http: HttpClient) { }

  public getCurrentMap(lat: number, lon: number): Observable<MapResponse> {
    const params = new HttpParams()
      .set('lat', lat)
      .set('lon', lon);

    return this.http.get<MapResponse>(`/api/map/current`, { params });
  }

  public processMapData(res: MapResponse): Record<string, number[][]> {
    const swappedData: Record<string, number[][]> = {};
    for (const key in res.map_data) {
      swappedData[key] = res.map_data[key].map(([lat, lon, val]) => [lon, lat, val]);
    }
    return swappedData;
  }
}
