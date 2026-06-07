import { useEffect, useState } from 'react';

export default function ScoreVisualizer({ response, isMentorMode }) {
  const [animatedScore, setAnimatedScore] = useState(0);

  // Extract score properly from either Person A or Person B response
  const isPersonA = response?.user_type === 'person_a';
  let targetScore = 0;

  if (isPersonA) {
    targetScore = response?.eligibility?.probability ? Math.round(response.eligibility.probability * 100) : 0;
  } else {
    targetScore = response?.readiness?.score || 0;
  }

  useEffect(() => {
    // Simple animation effect
    const duration = 1000;
    const steps = 30;
    const stepTime = duration / steps;
    const increment = targetScore / steps;
    let current = 0;

    const timer = setInterval(() => {
      current += increment;
      if (current >= targetScore) {
        setAnimatedScore(targetScore);
        clearInterval(timer);
      } else {
        setAnimatedScore(Math.round(current));
      }
    }, stepTime);

    return () => clearInterval(timer);
  }, [targetScore]);

  // Determine colors based on score thresholds (same logic used in backend roughly)
  const colorClass = (targetScore >= 75)
    ? (isMentorMode ? 'text-emerald-400' : 'text-emerald-500')
    : (targetScore >= 50)
      ? (isMentorMode ? 'text-yellow-400' : 'text-yellow-500')
      : (isMentorMode ? 'text-slate-400' : 'text-slate-400');

  const radius = 36;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (animatedScore / 100) * circumference;
  const label = isPersonA ? "Eligibility Score" : "Readiness Score";

  return (
    <div className="flex flex-col items-center justify-center">
      <div className="relative flex items-center justify-center w-24 h-24">
        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 80 80">
          <circle
            cx="40"
            cy="40"
            r={radius}
            stroke="currentColor"
            strokeWidth="6"
            fill="transparent"
            className={isMentorMode ? 'text-slate-700' : 'text-slate-100'}
          />
          <circle
            cx="40"
            cy="40"
            r={radius}
            stroke="currentColor"
            strokeWidth="6"
            fill="transparent"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className={`transition-all duration-1000 ease-out ${colorClass}`}
          />
        </svg>
        <div className="absolute flex flex-col items-center justify-center">
          <span className={`text-2xl font-bold ${isMentorMode ? 'text-slate-100' : 'text-slate-800'}`}>
            {animatedScore}
          </span>
        </div>
      </div>
      <span className={`text-[10px] uppercase font-semibold tracking-wider mt-2 ${isMentorMode ? 'text-slate-500' : 'text-slate-400'}`}>
        {label}
      </span>
    </div>
  );
}
