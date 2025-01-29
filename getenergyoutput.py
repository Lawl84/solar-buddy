import datetime
import math
import requests
from zoneinfo import ZoneInfo
from pysolar.solar import get_altitude, get_azimuth
from pysolar.radiation import get_radiation_direct


def get_cloud_cover(latitude, longitude, local_time):
    cloud_cover_mapping = {
        "Clear": 0,
        "Mostly Clear": 20,
        "Partly Cloudy": 50,
        "Mostly Cloudy": 75,
        "Overcast": 100,
    }

    floored_hour = local_time.replace(minute=0, second=0, microsecond=0)
    request_hour_str = floored_hour.strftime("%Y-%m-%dT%H:00:00Z") 
    grid_url = f"https://api.weather.gov/points/{latitude},{longitude}"

    try:
        grid_response = requests.get(grid_url, timeout=10)
        grid_response.raise_for_status()
        grid_data = grid_response.json()

        grid_x = grid_data["properties"]["gridX"]
        grid_y = grid_data["properties"]["gridY"]
        grid_office = grid_data["properties"]["gridId"]



        forecast_url = f"https://api.weather.gov/gridpoints/{grid_office}/{grid_x},{grid_y}/forecast/hourly"
        forecast_response = requests.get(forecast_url, timeout=10)
        forecast_response.raise_for_status()
        forecast_data = forecast_response.json()

        for period in forecast_data["properties"]["periods"]:
            period_time = period["startTime"]
            short_forecast = period["shortForecast"].strip().lower() 

            period_time = datetime.datetime.strptime(period_time, "%Y-%m-%dT%H:%M:%S%z").strftime("%Y-%m-%dT%H:00:00Z")

            if period_time == request_hour_str:
                for key, value in cloud_cover_mapping.items():
                    if short_forecast.startswith(key.lower()): 
                        print(f"Cloud Cover ({short_forecast}): {value}%")
                        return float(value)
                return 50.0 
        return 50.0

    except requests.exceptions.RequestException as e:
        return 50.0 





def calc_incidence_angle(sun_alt_deg, sun_az_deg, panel_zenith_deg, panel_azimuth_deg):
    alpha_sun = math.radians(sun_alt_deg)
    beta_panel = math.radians(90 - panel_zenith_deg)
    delta_az = math.radians(sun_az_deg - panel_azimuth_deg)

    cos_theta = (
        math.sin(alpha_sun) * math.cos(beta_panel) +
        math.cos(alpha_sun) * math.sin(beta_panel) * math.cos(delta_az)
    )

    cos_theta = max(min(cos_theta, 1.0), 0.0)
    return math.degrees(math.acos(cos_theta)), cos_theta





def estimate_solar_power_fixed(latitude, longitude, local_time, sun_alt_deg, sun_az_deg, dni_actual, cloud_factor, panel_width=0.05, panel_height=0.05, panel_efficiency=0.20, panel_zenith_deg=0.0, panel_azimuth_deg=180.0, diffuse_fraction=0.1):
    incidence_angle_deg, cos_inc = calc_incidence_angle(sun_alt_deg, sun_az_deg, panel_zenith_deg, panel_azimuth_deg)

    direct_irradiance = dni_actual * cos_inc

    beta_rad = math.radians(90 - panel_zenith_deg)
    diffuse_irradiance_clear = diffuse_fraction * dni_actual / cloud_factor if cloud_factor > 0 else 0
    diffuse_irradiance = diffuse_irradiance_clear * (1 + math.cos(beta_rad)) / 2.0 * cloud_factor

    total_irradiance = direct_irradiance + diffuse_irradiance

    panel_area = panel_width * panel_height
    power = total_irradiance * panel_area * panel_efficiency
    return power




def find_optimal_orientation(latitude, longitude, local_time, panel_width=0.05, panel_height=0.05, panel_efficiency=0.20,
                             diffuse_fraction=0.1):
    
    if local_time.tzinfo is None:
        local_time = local_time.replace(tzinfo=ZoneInfo("America/Phoenix"))
    utc_time = local_time.astimezone(datetime.timezone.utc)

    print(f"Local Arizona Time: {local_time}")


    sun_alt_deg = get_altitude(latitude, longitude, utc_time)
    sun_az_deg = get_azimuth(latitude, longitude, utc_time)

    print(f"Sun Altitude: {sun_alt_deg:.2f}°")
    print(f"Sun Azimuth: {sun_az_deg:.2f}°")



    cloud_cover_pct = get_cloud_cover(latitude, longitude, local_time)
    cloud_factor = max(1.0 - (cloud_cover_pct / 100.0), 0.0)

    dni_clear = get_radiation_direct(utc_time, sun_alt_deg)
    dni_actual = dni_clear * cloud_factor

    print(f"Adjusted DNI (After Clouds): {dni_actual:.2f} W/m²")

    best_power = 0.0
    best_zenith = None
    best_azimuth = None

    zenith_angles = range(0, 91, 1) 
    azimuth_angles = range(0, 361, 10)  

    for z in zenith_angles:
        for a in azimuth_angles:
            power = estimate_solar_power_fixed(latitude, longitude, local_time, sun_alt_deg, sun_az_deg,
                                               dni_actual, cloud_factor, panel_width, panel_height,
                                               panel_efficiency, panel_zenith_deg=z, panel_azimuth_deg=a,
                                               diffuse_fraction=diffuse_fraction)
            

            if power > best_power:
                best_power = power
                best_zenith = z
                best_azimuth = a

    return best_zenith, best_azimuth, best_power


def main(latitude, longitude): 

    az_local_time = datetime.datetime.now(ZoneInfo("America/Phoenix"))  

    best_zenith, best_azimuth, best_power = find_optimal_orientation(
        latitude, longitude, az_local_time)

    print(f"Optimal Zenith Angle: {best_zenith}")
    print(f"Optimal Azimuth Angle: {best_azimuth}")
    print(f"Maximum Power Output: {best_power} W")
    final_string = f"Optimal Zenith Angle: {best_zenith}\n" + f"Optimal Azimuth Angle: {best_azimuth}\n" + f"Maximum Power Output: {best_power:.4f} W\n"
    return final_string

if __name__ == "__main__":
    main()

