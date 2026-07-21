import { Injectable, inject } from '@angular/core';
import { delay, of, Observable } from 'rxjs';
import { Insight } from '../models/copilot.models';
import { CopilotStateService } from './copilot-state.service';

// ─────────────────────────────────────────────────────────────
// InsightsService
//
// Reads insights from the CopilotStateService cache — the full
// pipeline (including insights) already ran inside POST /query.
// Falls back to mock data when no cached response is available.
// ─────────────────────────────────────────────────────────────

@Injectable({ providedIn: 'root' })
export class InsightsService {
  private state = inject(CopilotStateService);

  // ── Read insights from cached BackendQueryResponse ───────
  // The backend computes insights as part of the NL→SQL→Execute
  // pipeline. We map them to the frontend Insight shape here.
  // Falls back to mock data when cache is empty.
  // --------------------------------------------------------
  generate(executionId: string): Observable<Insight[]> {
    const cached = this.state.lastResponse();
    if (cached?.result?.insights) {
      const ins = cached.result.insights;
      const insights: Insight[] = [
        // Summary as an info card
        ...(ins.summary ? [{ type: 'info' as const, icon: 'i', text: ins.summary }] : []),
        // Key insights
        ...ins.key_insights.map(k => ({
          type: this.categoryToType(k.category),
          icon: this.categoryToIcon(k.category),
          text: k.message,
        })),
        // Trends
        ...ins.trends.map(t => ({
          type: 'positive' as const,
          icon: 'up',
          text: t.message,
        })),
        // Anomalies
        ...ins.anomalies.map(a => ({
          type: 'warning' as const,
          icon: '!',
          text: a.message,
        })),
      ];
      return of(insights.slice(0, 5)); // cap at 5 cards
    }
    // ── Fallback to mock when no cached response ────────────
    return of(MOCK_INSIGHTS).pipe(delay(1200));
  }

  private categoryToType(category: string): Insight['type'] {
    if (category === 'anomaly' || category === 'warning') return 'warning';
    if (category === 'positive' || category === 'trend')  return 'positive';
    return 'info';
  }

  private categoryToIcon(category: string): string {
    if (category === 'anomaly' || category === 'warning') return '!';
    if (category === 'positive' || category === 'trend')  return 'up';
    return 'i';
  }
}

// ─────────────────────────────────────────────────────────────
//  MOCK DATA
// ─────────────────────────────────────────────────────────────

export const MOCK_INSIGHTS: Insight[] = [
  {
    type: 'warning',
    icon: '⚠',
    text: 'Notebook Pro X15 showed the largest drop (−39.9%). This coincides with the launch of competitor ModelX in August 2024. A pricing analysis is recommended.',
  },
  {
    type: 'info',
    icon: 'ℹ',
    text: 'The 3 products with the largest drops belong to the Premium Peripherals category, suggesting a category trend rather than isolated products.',
  },
  {
    type: 'positive',
    icon: '↑',
    text: 'Despite the revenue drops, unit sales volume for the affected products grew 8% — the revenue decline may be explained by aggressive Q3 promotions.',
  },
];
