import { useQuery } from '@tanstack/react-query';
import { Play, Square, Activity, Clock, List as ListIcon } from 'lucide-react';
import { daemonApi } from '../api/client';
import { format } from 'date-fns';

export default function DaemonControl() {
  const { data: status, isLoading } = useQuery({
    queryKey: ['daemonStatus'],
    queryFn: async () => {
      const response = await daemonApi.getStatus();
      return response.data;
    },
    refetchInterval: 3000,
  });

  const { data: logs } = useQuery({
    queryKey: ['daemonLogs'],
    queryFn: async () => {
      const response = await daemonApi.getLogs(50);
      return response.data;
    },
    refetchInterval: 5000,
  });

  if (isLoading) {
    return (
      <div className="p-8">
        <div className="animate-pulse">Loading daemon status...</div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-gray-800">Daemon Control</h2>
        <p className="text-gray-600 mt-1">Manage background automation daemon</p>
      </div>

      {/* Status Card */}
      <div className="bg-white rounded-lg shadow mb-6">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-800">Daemon Status</h3>
            <div className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${status?.is_running ? 'bg-green-500' : 'bg-gray-300'}`}></div>
              <span className={`font-medium ${status?.is_running ? 'text-green-600' : 'text-gray-500'}`}>
                {status?.is_running ? 'Running' : 'Stopped'}
              </span>
            </div>
          </div>
        </div>

        <div className="p-6">
          {status?.is_running ? (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="flex items-start gap-3">
                  <Activity className="text-blue-600 mt-1" size={20} />
                  <div>
                    <p className="text-sm font-medium text-gray-600">Search Criteria</p>
                    <p className="text-lg font-semibold text-gray-800">{status.search_criteria || 'N/A'}</p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <ListIcon className="text-purple-600 mt-1" size={20} />
                  <div>
                    <p className="text-sm font-medium text-gray-600">Queue Size</p>
                    <p className="text-lg font-semibold text-gray-800">{status.queue_size || 0}</p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <Clock className="text-orange-600 mt-1" size={20} />
                  <div>
                    <p className="text-sm font-medium text-gray-600">Applications Today</p>
                    <p className="text-lg font-semibold text-gray-800">
                      {status.applications_today || 0} / {status.max_applications_per_day || 0}
                    </p>
                  </div>
                </div>
              </div>

              {status.last_cycle_at && (
                <div className="pt-4 border-t border-gray-200">
                  <p className="text-sm text-gray-600">
                    Last cycle: {format(new Date(status.last_cycle_at), 'MMM d, yyyy h:mm:ss a')}
                  </p>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-8">
              <p className="text-gray-600 mb-4">Daemon is not running</p>
              <p className="text-sm text-gray-500">Use the CLI to start the daemon:</p>
              <code className="block mt-2 px-4 py-2 bg-gray-100 rounded text-sm">
                job-apply daemon start --criteria "Software Engineer" --max-daily 50
              </code>
            </div>
          )}
        </div>
      </div>

      {/* Control Buttons */}
      <div className="bg-white rounded-lg shadow mb-6 p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Actions</h3>
        <div className="flex gap-4">
          <button
            className="flex items-center gap-2 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50"
            disabled={status?.is_running}
          >
            <Play size={18} />
            Start Daemon
          </button>
          <button
            className="flex items-center gap-2 px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50"
            disabled={!status?.is_running}
          >
            <Square size={18} />
            Stop Daemon
          </button>
        </div>
        <p className="text-sm text-gray-500 mt-4">
          Note: Daemon management is best done via CLI for now. Web controls coming soon.
        </p>
      </div>

      {/* Recent Logs */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-800">Recent Logs</h3>
        </div>
        <div className="p-6">
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {logs && logs.length > 0 ? (
              logs.map((log: any) => (
                <div key={log.id} className="flex items-start gap-3 text-sm py-2 border-b border-gray-100 last:border-0">
                  <span className="text-gray-500 min-w-[140px]">
                    {format(new Date(log.timestamp), 'MMM d, h:mm:ss a')}
                  </span>
                  <span className={`font-medium min-w-[60px] ${
                    log.level === 'ERROR' ? 'text-red-600' :
                    log.level === 'WARNING' ? 'text-yellow-600' :
                    log.level === 'INFO' ? 'text-blue-600' :
                    'text-gray-600'
                  }`}>
                    {log.level}
                  </span>
                  <span className="text-gray-700 flex-1">{log.message}</span>
                </div>
              ))
            ) : (
              <p className="text-gray-500 text-center py-4">No logs available</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
