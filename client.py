import grpc
import weather_pb2
import weather_pb2_grpc
import logging

# Sample Input Data
time_series_data = weather_pb2.TimeSeriesData(
    dates=["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"],
    values=[100.0, 101.5, 102.7, 103.2, 104.8]
)

# Sample Prophet Parameters
model_parameters = weather_pb2.ProphetParameters(
    changepoint_prior_scale=0.05,
    seasonality_prior_scale=10.0,
    holidays_prior_scale=10.0,
    seasonality_mode="additive",
    yearly_seasonality=True,
    weekly_seasonality=True,
    daily_seasonality=False,
    growth="linear",
    n_changepoints=25,
    changepoint_range=0.8
)

# Create a ForecastRequest
forecast_request = weather_pb2.ForecastRequest(
    data=time_series_data,
    periods=10,  # Forecast 10 future days
    model_parameters=model_parameters,
    return_components=True
)

def run():
    """Connects to the gRPC server and requests a forecast."""
    with grpc.insecure_channel("localhost:50051") as channel:
        stub = weather_pb2_grpc.ForecastDataStub(channel)
        
        try:
            response = stub.CreateForecast(forecast_request)
            print("\nForecast Results:")
            print("Dates:", response.forecast_dates)
            print("Values:", response.forecast_values)
            print("Lower Bound:", response.forecast_lower_bound)
            print("Upper Bound:", response.forecast_upper_bound)

            if response.components:
                print("\nForecast Components:")
                for key, value in response.components.component.items():
                    print(f"{key}: {value}")

        except grpc.RpcError as e:
            logging.error(f"gRPC Error: {e.details()}")
            print(f"Error Code: {e.code()}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
