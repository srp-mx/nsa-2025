export interface MapResponse {
  latitude: number;
  longitude: number;
  radius_km: number;
  start_date: string;
  end_date: string;
  map_data: Record<string, number[][]>;
  products: Record<string, ProductStats>;
}

export interface ProductStats {
  mean_value: number;
  min_value: number;
  max_value: number;
  data_points: number;
  units: string;
}
