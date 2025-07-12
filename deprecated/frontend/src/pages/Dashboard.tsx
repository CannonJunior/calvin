import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { analyticsApi, earningsApi, predictionsApi } from '@/services/api';
import LoadingSpinner from '@/components/LoadingSpinner';
import { 
  ChartBarIcon, 
  CalendarIcon, 
  PresentationChartLineIcon,
  TrendingUpIcon,
  TrendingDownIcon,
} from '@heroicons/react/24/outline';
import { format, addDays } from 'date-fns';

export default function Dashboard() {
  const { data: dashboardStats, isLoading: statsLoading } = useQuery({
    queryKey: ['dashboard-overview'],
    queryFn: () => analyticsApi.getDashboardOverview().then(res => res.data),
  });

  const { data: upcomingEarnings, isLoading: earningsLoading } = useQuery({
    queryKey: ['upcoming-earnings'],
    queryFn: () => earningsApi.getCalendar({
      start_date: format(new Date(), 'yyyy-MM-dd'),
      end_date: format(addDays(new Date(), 7), 'yyyy-MM-dd'),
    }).then(res => res.data),
  });

  const { data: upcomingPredictions, isLoading: predictionsLoading } = useQuery({
    queryKey: ['upcoming-predictions'],
    queryFn: () => predictionsApi.getUpcoming({ 
      days_ahead: 7,
      confidence_threshold: 0.6 
    }).then(res => res.data),
  });

  if (statsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600">
          AI-powered S&P 500 earnings predictions and market analysis
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="card">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 rounded-lg">
              <ChartBarIcon className="h-6 w-6 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">S&P 500 Companies</p>
              <p className="text-2xl font-bold text-gray-900">
                {dashboardStats?.total_sp500_companies || 0}
              </p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="p-2 bg-green-100 rounded-lg">
              <CalendarIcon className="h-6 w-6 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Upcoming Earnings (7d)</p>
              <p className="text-2xl font-bold text-gray-900">
                {dashboardStats?.upcoming_earnings_7d || 0}
              </p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="p-2 bg-purple-100 rounded-lg">
              <PresentationChartLineIcon className="h-6 w-6 text-purple-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Prediction Accuracy</p>
              <p className="text-2xl font-bold text-gray-900">
                {((dashboardStats?.recent_prediction_accuracy || 0) * 100).toFixed(1)}%
              </p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="p-2 bg-yellow-100 rounded-lg">
              <TrendingUpIcon className="h-6 w-6 text-yellow-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Market Sentiment</p>
              <p className="text-2xl font-bold text-gray-900">
                {dashboardStats?.market_sentiment?.overall_score?.toFixed(1) || 'N/A'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Upcoming Earnings */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-medium text-gray-900">
              Upcoming Earnings (Next 7 Days)
            </h2>
            <CalendarIcon className="h-5 w-5 text-gray-400" />
          </div>
          
          {earningsLoading ? (
            <div className="flex justify-center py-8">
              <LoadingSpinner />
            </div>
          ) : (
            <div className="space-y-3">
              {upcomingEarnings?.slice(0, 5).map((earning) => (
                <div
                  key={`${earning.company_symbol}-${earning.earnings_date}`}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div>
                    <p className="font-medium text-gray-900">
                      {earning.company_symbol}
                    </p>
                    <p className="text-sm text-gray-600">
                      {format(new Date(earning.earnings_date), 'MMM dd, yyyy')}
                    </p>
                  </div>
                  <div className="text-right">
                    {earning.has_prediction && (
                      <div className="flex items-center space-x-2">
                        {earning.predicted_direction === 'UP' ? (
                          <TrendingUpIcon className="h-4 w-4 text-green-500" />
                        ) : earning.predicted_direction === 'DOWN' ? (
                          <TrendingDownIcon className="h-4 w-4 text-red-500" />
                        ) : (
                          <div className="h-4 w-4 bg-gray-400 rounded-full" />
                        )}
                        <span className="text-sm text-gray-600">
                          {((earning.prediction_confidence || 0) * 100).toFixed(0)}%
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
              
              {(!upcomingEarnings || upcomingEarnings.length === 0) && (
                <p className="text-gray-500 text-center py-8">
                  No upcoming earnings found
                </p>
              )}
            </div>
          )}
        </div>

        {/* Recent Predictions */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-medium text-gray-900">
              High Confidence Predictions
            </h2>
            <PresentationChartLineIcon className="h-5 w-5 text-gray-400" />
          </div>
          
          {predictionsLoading ? (
            <div className="flex justify-center py-8">
              <LoadingSpinner />
            </div>
          ) : (
            <div className="space-y-3">
              {upcomingPredictions?.by_date && 
                Object.entries(upcomingPredictions.by_date)
                  .slice(0, 5)
                  .map(([date, predictions]: [string, any]) => (
                    <div key={date} className="border-l-4 border-blue-500 pl-4">
                      <p className="text-sm font-medium text-gray-900">
                        {format(new Date(date), 'MMM dd, yyyy')}
                      </p>
                      <div className="mt-1 space-y-1">
                        {[...predictions.UP, ...predictions.DOWN, ...predictions.NEUTRAL]
                          .slice(0, 3)
                          .map((pred: any, idx: number) => (
                            <div key={idx} className="flex items-center justify-between">
                              <span className="text-sm text-gray-600">
                                {pred.symbol}
                              </span>
                              <div className="flex items-center space-x-2">
                                <span className={`text-sm ${
                                  pred.predicted_return > 0 ? 'text-green-600' : 
                                  pred.predicted_return < 0 ? 'text-red-600' : 
                                  'text-gray-600'
                                }`}>
                                  {(pred.predicted_return * 100).toFixed(1)}%
                                </span>
                                <span className="text-xs text-gray-500">
                                  {(pred.confidence * 100).toFixed(0)}%
                                </span>
                              </div>
                            </div>
                          ))}
                      </div>
                    </div>
                  ))}
              
              {(!upcomingPredictions || 
                Object.keys(upcomingPredictions.by_date || {}).length === 0) && (
                <p className="text-gray-500 text-center py-8">
                  No predictions available
                </p>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Market Sentiment Overview */}
      {dashboardStats?.market_sentiment && (
        <div className="card">
          <h2 className="text-lg font-medium text-gray-900 mb-4">
            Market Sentiment Overview
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {(dashboardStats.market_sentiment.bullish_percentage || 0).toFixed(1)}%
              </div>
              <div className="text-sm text-gray-600">Bullish</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-600">
                {(dashboardStats.market_sentiment.neutral_percentage || 0).toFixed(1)}%
              </div>
              <div className="text-sm text-gray-600">Neutral</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">
                {(dashboardStats.market_sentiment.bearish_percentage || 0).toFixed(1)}%
              </div>
              <div className="text-sm text-gray-600">Bearish</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}