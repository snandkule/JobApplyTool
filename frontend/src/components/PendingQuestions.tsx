import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Sparkles, Check, X } from 'lucide-react';
import { questionsApi } from '../api/client';
import { format } from 'date-fns';

export default function PendingQuestions() {
  const queryClient = useQueryClient();
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [suggestions, setSuggestions] = useState<Record<number, string>>({});

  const { data: questions, isLoading } = useQuery({
    queryKey: ['pendingQuestions'],
    queryFn: async () => {
      const response = await questionsApi.listPending('pending', 100);
      return response.data;
    },
    refetchInterval: 5000,
  });

  const answerMutation = useMutation({
    mutationFn: (data: { question_id: number; answer: string }) =>
      questionsApi.answerQuestion({ ...data, save_to_kb: true, reuse_policy: 'always_same' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pendingQuestions'] });
      queryClient.invalidateQueries({ queryKey: ['appStats'] });
    },
  });

  const suggestionMutation = useMutation({
    mutationFn: (data: { question_text: string; job_id?: number; field_type: string }) =>
      questionsApi.getSuggestion(data),
    onSuccess: (response, variables) => {
      const questionId = questions?.find((q: any) => q.question_text === variables.question_text)?.id;
      if (questionId) {
        setSuggestions(prev => ({ ...prev, [questionId]: response.data.suggestion }));
      }
    },
  });

  const handleAnswer = (questionId: number) => {
    const answer = answers[questionId];
    if (answer) {
      answerMutation.mutate({ question_id: questionId, answer });
      setAnswers(prev => {
        const newAnswers = { ...prev };
        delete newAnswers[questionId];
        return newAnswers;
      });
    }
  };

  const handleGetSuggestion = (question: any) => {
    suggestionMutation.mutate({
      question_text: question.question_text,
      job_id: question.job_id,
      field_type: question.field_type,
    });
  };

  const handleUseSuggestion = (questionId: number) => {
    const suggestion = suggestions[questionId];
    if (suggestion) {
      setAnswers(prev => ({ ...prev, [questionId]: suggestion }));
    }
  };

  if (isLoading) {
    return (
      <div className="p-8">
        <div className="animate-pulse">Loading questions...</div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-gray-800">Pending Questions</h2>
        <p className="text-gray-600 mt-1">Answer questions to resume paused applications</p>
      </div>

      {questions && questions.length > 0 ? (
        <div className="space-y-4">
          {questions.map((question: any) => (
            <div key={question.id} className="bg-white rounded-lg shadow p-6">
              <div className="mb-4">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <h4 className="text-lg font-medium text-gray-800 mb-1">
                      {question.question_text}
                    </h4>
                    {question.job && (
                      <p className="text-sm text-gray-600">
                        {question.job.company} - {question.job.title}
                      </p>
                    )}
                  </div>
                  <span className="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-800 rounded">
                    {question.field_type}
                  </span>
                </div>
                <p className="text-xs text-gray-500">
                  Asked {format(new Date(question.created_at), 'MMM d, yyyy h:mm a')}
                </p>
              </div>

              {/* AI Suggestion */}
              {suggestions[question.id] && (
                <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded">
                  <div className="flex items-start gap-2">
                    <Sparkles size={16} className="text-blue-600 mt-1" />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-blue-800 mb-1">AI Suggestion:</p>
                      <p className="text-sm text-blue-700">{suggestions[question.id]}</p>
                      <button
                        onClick={() => handleUseSuggestion(question.id)}
                        className="mt-2 text-xs text-blue-600 hover:text-blue-800 font-medium"
                      >
                        Use this suggestion
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Answer Input */}
              <div className="flex gap-2">
                {question.field_type === 'yes_no' ? (
                  <div className="flex gap-2 flex-1">
                    <button
                      onClick={() => setAnswers(prev => ({ ...prev, [question.id]: 'yes' }))}
                      className={`flex-1 px-4 py-2 border rounded transition-colors ${
                        answers[question.id] === 'yes'
                          ? 'bg-green-600 text-white border-green-600'
                          : 'border-gray-300 hover:border-green-600'
                      }`}
                    >
                      Yes
                    </button>
                    <button
                      onClick={() => setAnswers(prev => ({ ...prev, [question.id]: 'no' }))}
                      className={`flex-1 px-4 py-2 border rounded transition-colors ${
                        answers[question.id] === 'no'
                          ? 'bg-red-600 text-white border-red-600'
                          : 'border-gray-300 hover:border-red-600'
                      }`}
                    >
                      No
                    </button>
                  </div>
                ) : (
                  <input
                    type={question.field_type === 'number' ? 'number' : 'text'}
                    placeholder="Enter your answer..."
                    value={answers[question.id] || ''}
                    onChange={(e) => setAnswers(prev => ({ ...prev, [question.id]: e.target.value }))}
                    className="flex-1 px-4 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500"
                  />
                )}

                <button
                  onClick={() => handleGetSuggestion(question)}
                  disabled={suggestionMutation.isPending}
                  className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 transition-colors disabled:opacity-50 flex items-center gap-2"
                  title="Get AI suggestion"
                >
                  <Sparkles size={18} />
                  AI
                </button>

                <button
                  onClick={() => handleAnswer(question.id)}
                  disabled={!answers[question.id] || answerMutation.isPending}
                  className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition-colors disabled:opacity-50 flex items-center gap-2"
                >
                  <Check size={18} />
                  Submit
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <p className="text-lg text-gray-600">No pending questions!</p>
          <p className="text-sm text-gray-500 mt-2">All applications are proceeding smoothly.</p>
        </div>
      )}
    </div>
  );
}
