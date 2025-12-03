import React, { useEffect, useState } from 'react';
import io, { Socket } from 'socket.io-client';

interface OverconsumptionAlert {
  user_id: string;
  device_id: number;
  consumption: number;
  threshold: number;
  message: string;
  timestamp: string;
}

interface OverconsumptionAlertProps {
  userId: string;
}

export const OverconsumptionAlertListener: React.FC<OverconsumptionAlertProps> = ({ userId }) => {
  const [alert, setAlert] = useState<OverconsumptionAlert | null>(null);
  const [socket, setSocket] = useState<Socket | null>(null);

  useEffect(() => {
    console.log('[OverconsumptionAlert] Initializing for user:', userId);
    
    const socketConnection = io('/', {
      path: '/socket.io',
      transports: ['polling']
    });

    socketConnection.on('connect', () => {
      console.log('[OverconsumptionAlert] Socket connected:', socketConnection.id);
    });

    socketConnection.on('connect_error', (error: any) => {
      console.error('[OverconsumptionAlert] Connection error:', error);
    });

    socketConnection.on('overconsumption_notification', (data: OverconsumptionAlert) => {
      console.log('[OverconsumptionAlert] Notification received:', data);
      console.log('[OverconsumptionAlert] Current user ID:', userId);
      console.log('[OverconsumptionAlert] Notification user ID:', data.user_id);
      console.log('[OverconsumptionAlert] Match:', data.user_id === userId);
      
      if (data.user_id === userId) {
        console.log('[OverconsumptionAlert] Setting alert for display');
        setAlert(data);
        
        // Auto-dismiss after 10 seconds
        setTimeout(() => {
          console.log('[OverconsumptionAlert] Auto-dismissing alert');
          setAlert(null);
        }, 10000);
      } else {
        console.log('[OverconsumptionAlert] Alert not for this user, ignoring');
      }
    });

    setSocket(socketConnection);

    return () => {
      console.log('[OverconsumptionAlert] Disconnecting socket');
      socketConnection.disconnect();
    };
  }, [userId]);

  if (!alert) return null;

  return (
    <div className="fixed top-4 right-4 z-[9999] animate-in slide-in-from-top-2">
      <div className="bg-red-600 text-white rounded-lg shadow-2xl p-4 min-w-[350px] max-w-md border-2 border-red-700">
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0 mt-0.5">
            <svg 
              className="w-6 h-6" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth={2} 
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" 
              />
            </svg>
          </div>
          <div className="flex-1">
            <h3 className="font-bold text-lg mb-1">⚠️ Overconsumption Alert!</h3>
            <p className="text-sm mb-2">{alert.message}</p>
            <div className="text-xs opacity-90 space-y-1">
              <div>Device ID: {alert.device_id}</div>
              <div>Current: {alert.consumption.toFixed(2)} kWh</div>
              <div>Limit: {alert.threshold.toFixed(2)} kWh</div>
              <div className="mt-2 pt-2 border-t border-red-500">
                {new Date(alert.timestamp).toLocaleString()}
              </div>
            </div>
          </div>
          <button
            onClick={() => setAlert(null)}
            className="flex-shrink-0 text-white hover:text-red-200 transition-colors"
          >
            <svg 
              className="w-5 h-5" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth={2} 
                d="M6 18L18 6M6 6l12 12" 
              />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
};
