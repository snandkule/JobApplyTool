import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Trash2, ExternalLink, Star } from 'lucide-react';
import { jobsApi } from '../api/client';
import { format } from 'date-fns';

export default function ApplicationQueue() {
  const queryClient = useQueryClient();

  const { data: queue, isLoading } = useQuery({
    queryKey: ['queue'],
    queryFn: async () => {
      const response = await jobsApi.listQueue('queued', 100);
      return response.data;
    },
    refetchInterval: 5000,
  });

  const removeMutation = useMutation({
    mutationFn: (queueId: number) => jobsApi.removeFromQueue(queueId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['queue'] });
    },
  });

  if (isLoading) {
    return (
      <div className="p-8">
        <div className="animate-pulse">Loading queue...</div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-gray-800">Application Queue</h2>
        <p className="text-gray-600 mt-1">Jobs queued for automated application</p>
      </div>

      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-800">
              {queue?.length || 0} jobs in queue
            </h3>
            <span className="text-sm text-gray-500">
              Sorted by priority and date
            </span>
          </div>
        </div>

        <div className="divide-y divide-gray-200">
          {queue && queue.length > 0 ? (
            queue.map((item: any) => (
              <div key={item.queue_id} className="px-6 py-4 hover:bg-gray-50">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h4 className="text-lg font-medium text-gray-800">
                        {item.job.title}
                      </h4>
                      <span className="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded">
                        {item.job.platform}
                      </span>
                      {item.match_score && (
                        <span className={`px-2 py-1 text-xs font-medium rounded ${
                          item.match_score >= 0.8 ? 'bg-green-100 text-green-800' :
                          item.match_score >= 0.6 ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {Math.round(item.match_score * 100)}% match
                        </span>
                      )}
                    </div>

                    <p className="text-gray-600 mb-2">{item.job.company}</p>

                    <div className="flex items-center gap-4 text-sm text-gray-500">
                      <span>{item.job.location || 'Location not specified'}</span>
                      <span>•</span>
                      <span>Added {format(new Date(item.added_at), 'MMM d, yyyy h:mm a')}</span>
                      <span>•</span>
                      <div className="flex items-center gap-1">
                        <Star size={14} fill={item.priority >= 7 ? '#fbbf24' : 'none'} className="text-yellow-500" />
                        <span>Priority: {item.priority}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => removeMutation.mutate(item.queue_id)}
                      className="p-2 text-red-600 hover:bg-red-50 rounded transition-colors"
                      title="Remove from queue"
                    >
                      <Trash2 size={18} />
                    </button>
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="px-6 py-12 text-center text-gray-500">
              <p className="text-lg">No jobs in queue</p>
              <p className="text-sm mt-2">Use the CLI to add jobs to the queue</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
