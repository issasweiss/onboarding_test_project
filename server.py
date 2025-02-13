import grpc 
import weather_pb2
import weather_pb2_grpc
from concurrent import futures
import time
import logging
import pandas as pd
import weather_pb2_grpc
import weather_pb2
from prophet import Prophet
import app

class ForecastData(weather_pb2_grpc.ForecastDataServicer):
    async def CreateForecast(self, request, context): 
        try:
            # Prepare the input data
            df = pd.DataFrame({"ds": request.data.dates, "y": request.data.values}) 
            df['ds'] = pd.to_datetime(df['ds'])
            
            # Handle missing model parameters
            if not request.HasField("model_parameters"):
                model_params = weather_pb2.ProphetParameters()
            else:
                model_params = request.model_parameters
            
            # Configure and train the model
            model = Prophet(
                changepoint_prior_scale=model_params.changepoint_prior_scale,
                seasonality_prior_scale=model_params.seasonality_prior_scale,
                holidays_prior_scale=model_params.holidays_prior_scale,
                seasonality_mode=model_params.seasonality_mode,
                yearly_seasonality=model_params.yearly_seasonality,
                weekly_seasonality=model_params.weekly_seasonality,
                daily_seasonality=model_params.daily_seasonality,
                growth=model_params.growth
            )
            model.fit(df)
            
            # Create future dates for forecasting
            future = model.make_future_dataframe(periods=request.periods)
            
            # If using logistic growth, set cap and floor for future dates
            if model_params.growth == 'logistic':
                future['cap'] = model_params.cap
                future['floor'] = model_params.floor
            
            # Make predictions
            forecast = model.predict(future)
            
            # Prepare the response
            response = weather_pb2.ForecastResponse(
                forecast_dates=forecast.ds[-request.periods:].dt.strftime('%Y-%m-%d').tolist(),
                forecast_values=forecast.yhat[-request.periods:].tolist(),
                forecast_lower_bound=forecast.yhat_lower[-request.periods:].tolist(),
                forecast_upper_bound=forecast.yhat_upper[-request.periods:].tolist()
            )
            
            # Add components if requested
            if request.return_components:
                components = {
                    'trend': forecast.trend[-request.periods:].tolist(),
                    'yearly': forecast.yearly[-request.periods:].tolist() if 'yearly' in forecast else None,
                    'weekly': forecast.weekly[-request.periods:].tolist() if 'weekly' in forecast else None,
                    'daily': forecast.daily[-request.periods:].tolist() if 'daily' in forecast else None
                }
                for key, values in components.items():
                    if values is not None:
                        response.components.component[key] = values[-1]  # Take the last value
            
            return response
        
        except Exception as e:
            logging.error(f"Error in CreateForecast: {str(e)}")
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def GetDefaultParameters(self, request, context):
        return weather_pb2.ProphetParameters()
            
        
        