import { useQuery } from '@tanstack/react-query';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { TrendingUp, CheckCircle, Clock, XCircle, Activity } from 'lucide-react';
import { applicationsApi } from '../api/client';

const COLORS = ['#10b981', '#f59e0b', '#ef4444'];

export default function Dashboard() {
  const { data: stats } = useQuery({
    queryKey: ['appStats'],
    queryFn: async () => {
      const response = await applicationsApi.getStats();
      return response.data;
    },
    refetchInterval: 5000,
  });

  const { data: dailyStats } = useQuery({
    queryKey: ['dailyStats'],
    queryFn: async () => {
      const response = await applicationsApi.getDailyStats(30);
      return response.data;
    },
  });

  const { data: platformStats } = useQuery({
    queryKey: ['platformStats'],
    queryFn: async () => {
      const response = await applicationsApi.getPlatformStats();
      return response.data;
    },
  });

  const pieData = stats ? [
    { name: 'Submitted', value: stats.submitted },
    { name: 'Pending', value: stats.pending_questions },
    { name: 'Failed', value: stats.failed },
  ] : [];

  return (
    <div className="p-8">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-gray-800">Dashboard</h2>
        <p className="text-gray-600 mt-1">Overview of your job application automation</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          title="Total Applications"
          value={stats?.total_applications || 0}
          icon={<Activity className="text-blue-600" />}
          color="blue"
        />
        <StatCard
          title="Submitted"
          value={stats?.submitted || 0}
          icon={<CheckCircle className="text-green-600" />}
          color="green"
        />
        <StatCard
          title="Pending Questions"
          value={stats?.pending_questions || 0}
          icon={<Clock className="text-yellow-600" />}
          color="yellow"
        />
        <StatCard
          title="Success Rate"
          value={`${stats?.success_rate || 0}%`}
          icon={<TrendingUp className="text-purple-600" />}
          color="purple"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Daily Applications Chart */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Applications Over Time (30 Days)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={dailyStats || []}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" tickFormatter={(date) => new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} />
              <YAxis />
              <Tooltip labelFormatter={(date) => new Date(date).toLocaleDateString()} />
              <Line type="monotone" dataKey="applications_submitted" stroke="#10b981" strokeWidth={2} name="Submitted" />
              <Line type="monotone" dataKey="applications_failed" stroke="#ef4444" strokeWidth={2} name="Failed" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Status Distribution */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Application Status Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: ${value}`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {pieData.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Platform Stats */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Applications by Platform</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {platformStats?.map((platform: any) => (
            <div key={platform.platform} className="border rounded-lg p-4">
              <h4 className="font-medium text-gray-700 capitalize mb-2">{platform.platform}</h4>
              <div className="space-y-1">
                <p className="text-sm text-gray-600">Total: <span className="font-semibold">{platform.total}</span></p>
                <p className="text-sm text-gray-600">Submitted: <span className="font-semibold text-green-600">{platform.submitted}</span></p>
                <p className="text-sm text-gray-600">Success Rate: <span className="font-semibold">{platform.success_rate}%</span></p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Quick Stats */}
      <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="font-medium text-blue-800 mb-2">Today's Activity</h4>
          <p className="text-2xl font-bold text-blue-600">{stats?.applications_today || 0}</p>
          <p className="text-sm text-blue-600">applications submitted today</p>
        </div>
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <h4 className="font-medium text-green-800 mb-2">This Week</h4>
          <p className="text-2xl font-bold text-green-600">{stats?.applications_this_week || 0}</p>
          <p className="text-sm text-green-600">applications submitted this week</p>
        </div>
      </div>
    </div>
  );
}

function StatCard({ title, value, icon, color }: { title: string; value: number | string; icon: React.ReactNode; color: string }) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-600">{title}</h3>
        {icon}
      </div>
      <p className={`text-3xl font-bold text-${color}-600`}>{value}</p>
    </div>
  );
}
