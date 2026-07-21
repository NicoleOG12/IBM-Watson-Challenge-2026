// ============================================================
// chat.component.ts  — Thread de conversa principal
//
// Fluxo completo (mock → real):
//   1. Usuário envia pergunta   → POST /api/copilot/ask
//   2. Pipeline NLU steps       → POST /api/copilot/interpret
//   3. Catálogo resolvido       → GET  /api/catalog/resolve
//   4. SQL gerado               → POST /api/sql/generate
//   5. Validação segurança      → POST /api/sql/validate
//   6. Estimativa de custo      → POST /api/sql/estimate-cost
//   7. Execução (aprovação user)→ POST /api/query/execute
//   8. Resultados               → GET  /api/query/results/:executionId
//   9. Insights                 → POST /api/insights/generate
//  10. Próximos passos          → GET  /api/copilot/next-steps?executionId=
// ============================================================
import {
  Component, OnInit, AfterViewChecked,
  ElementRef, ViewChild, inject, signal
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { CopilotService } from '../../services/copilot.service';
import { SqlService }     from '../../services/sql.service';
import { QueryService }   from '../../services/query.service';
import { InsightsService } from '../../services/insights.service';
import { OutputsService }  from '../../services/outputs.service';
import { ActionsService }  from '../../services/actions.service';
import { QuestionsService } from '../../services/questions.service';

import type {
  ChatMessage, PipelineStep, SqlPreview,
  QueryResult, Insight, OutputType, ActionType
} from '../../models/copilot.models';

// ─────────────────────────────────────────────────────────
//  Quick-question chips exibidos acima do input
//  MOCK: array estático
//  REAL: GET /api/questions/suggested?userId=
// ─────────────────────────────────────────────────────────
const SUGGESTED_CHIPS = [
  'Top 10 customers by revenue',
  'Average ticket by channel',
  'Churn rate this month',
  'Critical stock levels',
  'Current delinquency rate',
];

// Estado do fluxo de execução por sessão
type FlowState = 'idle' | 'thinking' | 'preview' | 'executing' | 'done' | 'error';

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './chat.component.html',
  styleUrl: './chat.component.css',
})
export class ChatComponent implements OnInit, AfterViewChecked {
  @ViewChild('chatEnd') private chatEnd!: ElementRef<HTMLDivElement>;

  private copilotSvc  = inject(CopilotService);
  private sqlSvc      = inject(SqlService);
  private querySvc    = inject(QueryService);
  private insightsSvc = inject(InsightsService);
  private outputsSvc  = inject(OutputsService);
  private actionsSvc  = inject(ActionsService);
  private questionsSvc = inject(QuestionsService);

  // ── State signals ────────────────────────────────────────
  messages   = signal<ChatMessage[]>([]);
  flowState  = signal<FlowState>('idle');
  inputText  = '';
  chips      = SUGGESTED_CHIPS;

  // ── SQL inline editing state ──────────────────────────────
  editingSqlMsgId = '';   // id of the message whose SQL is being edited
  editedSqlDraft  = '';   // draft text while the editor is open

  // armazena contexto entre steps do fluxo
  private currentSessionId  = '';
  private currentExecutionId = '';
  private currentSql        = '';

  // ── Init: mensagem de boas-vindas ────────────────────────
  ngOnInit(): void {
    this.messages.set([{
      id: 'greeting',
      role: 'bob',
      time: this.now(),
      text: 'Hello! I\'m <strong>Bob</strong>, your corporate data copilot. Ask a question in plain language and I\'ll handle the rest — identify the tables, generate the SQL, estimate the cost, execute, and analyse the results.',
    }]);

    // ── MOCK: chips estáticos acima ──────────────────────────
    // ── REAL → descomente abaixo e remova o array estático ──
    // this.questionsSvc.getSuggested('alex.rodrigues@acme.com')
    //   .subscribe(s => this.chips = s);
  }

  ngAfterViewChecked(): void {
    this.chatEnd?.nativeElement.scrollIntoView({ behavior: 'smooth' });
  }

  // ── Envia pergunta do input ou clica em chip ─────────────
  sendMessage(question?: string): void {
    const q = (question ?? this.inputText).trim();
    if (!q || this.flowState() !== 'idle') return;
    this.inputText = '';
    this.addUserMessage(q);
    this.runFlow(q);
  }

  // ── Executa query aprovada pelo usuário ──────────────────
  executeQuery(): void {
    if (this.flowState() !== 'preview') return;
    this.flowState.set('executing');

    // ── Update execution step to 'active' ─────────────────
    this.updateStepStatus('Awaiting execution', 'active');

    // ── POST /api/query/execute { sessionId, sql, engine } ──
    this.querySvc.execute(this.currentSessionId, this.currentSql).subscribe(result => {
      this.currentExecutionId = result.executionId;
      this.updateStepStatus('Awaiting execution', 'done');
      this.addResultMessage(result);
      this.generateInsights(result.executionId);
    });
  }

  // ── Toggle SQL inline editor ─────────────────────────────
  toggleEditSql(msgId: string, currentSql: string): void {
    if (this.editingSqlMsgId === msgId) {
      // close without saving
      this.editingSqlMsgId = '';
      this.editedSqlDraft  = '';
    } else {
      this.editingSqlMsgId = msgId;
      this.editedSqlDraft  = currentSql;
    }
  }

  // ── Confirma edição manual do SQL ────────────────────────
  confirmEditSql(msgId: string): void {
    const newSql = this.editedSqlDraft.trim();
    if (!newSql) return;
    this.currentSql = newSql;
    // Patch the sqlPreview.sql in the message list
    this.messages.update(msgs =>
      msgs.map(m =>
        m.id === msgId && m.sqlPreview
          ? { ...m, sqlPreview: { ...m.sqlPreview, sql: newSql } }
          : m,
      ),
    );
    this.editingSqlMsgId = '';
    this.editedSqlDraft  = '';
  }

  // ── Integrar com banco do cliente ────────────────────────
  integrateWithClientDb(): void {
    // REAL → POST /api/integrations/connect { executionId }
    this.addBobMessage('Integration request sent. Our team will be in touch to configure access to the client database.');
  }

  // ── Cancela sessão ───────────────────────────────────────
  cancelQuery(): void {
    // ── DELETE /api/query/cancel/:sessionId ─────────────────
    this.querySvc.cancel(this.currentSessionId).subscribe(() => {
      this.flowState.set('idle');
      this.addBobMessage('Query cancelled. You can ask a new question.');
    });
  }

  // ── Gera output (resumo executivo / dashboard / diário) ──
  generateOutput(type: OutputType): void {
    // ── POST /api/outputs/generate { type, executionId } ─────
    this.outputsSvc.generate(type, this.currentExecutionId).subscribe(out => {
      const labels: Record<OutputType, string> = {
        executive_summary: 'Executive Summary',
        dashboard: 'Dashboard',
        logbook: 'Logbook',
      };
      this.addBobMessage(`<strong>${labels[type]}</strong> generated successfully. <a href="${out.url}" target="_blank">Open ↗</a>`);
    });
  }

  // ── Executa ação (Jira, e-mail, etc.) ────────────────────
  triggerAction(actionType: ActionType): void {
    // ── POST /api/actions/trigger { actionType, context: executionId } ──
    this.actionsSvc.trigger(actionType, this.currentExecutionId).subscribe(res => {
      this.addBobMessage(res.message + (res.externalId ? ` (${res.externalId})` : ''));
    });
  }

  // ── Salva pergunta no repositório ────────────────────────
  saveQuestion(): void {
    // ── POST /api/questions/save { question, sql, tags } ─────
    this.questionsSvc.save({
      question: 'Sales drop Q3 vs Q2',
      sql: this.currentSql,
      tags: ['Sales Analytics'],
      validated: true,
    }).subscribe(() => {
      this.addBobMessage('Question saved to the saved questions repository. ✓');
    });
  }

  // ── Clica em próximo passo sugerido ──────────────────────
  sendNextStep(suggestion: string): void {
    this.sendMessage(suggestion);
  }

  // ─────────────────────────────────────────────────────────
  //  FLUXO PRINCIPAL (orquestrado no front durante mock)
  //  Em produção: substituir por chamada única a POST /api/copilot/ask
  //  que retorna SSE ou polling de status
  // ─────────────────────────────────────────────────────────
  private runFlow(question: string): void {
    this.flowState.set('thinking');

    // ── STEP 1: POST /api/copilot/ask ─────────────────────
    this.copilotSvc.ask(question).subscribe({
      next: ({ sessionId }) => {
        this.currentSessionId = sessionId;

        // ── STEP 2: POST /api/copilot/interpret ──────────
        this.copilotSvc.interpret(question).subscribe(steps => {
          this.addStepsMessage(steps);

          // ── STEP 3+4+5: POST /api/sql/generate ─────────
          this.sqlSvc.generate(question).subscribe(preview => {
            this.currentSql = preview.sql;
            this.addSqlPreviewMessage(preview);
            this.flowState.set('preview');
          });
        });
      },
      error: (err: Error) => {
        this.flowState.set('idle');
        this.addBobMessage(
          `🔒 <strong>Operation not permitted.</strong><br>${err.message}`
        );
      },
    });
  }

  // ─────────────────────────────────────────────────────────
  //  Gera insights após execução
  // ─────────────────────────────────────────────────────────
  private generateInsights(executionId: string): void {
    // ── POST /api/insights/generate { executionId, context } ──
    this.insightsSvc.generate(executionId).subscribe(insights => {
      this.addInsightsMessage(insights);

      // ── GET /api/copilot/next-steps?executionId= ──────────
      this.copilotSvc.getNextSteps(executionId).subscribe(steps => {
        this.addNextStepsMessage(steps);
        this.flowState.set('idle');
      });
    });
  }

  // ─────────────────────────────────────────────────────────
  //  Helpers para construir mensagens
  // ─────────────────────────────────────────────────────────
  private addUserMessage(text: string): void {
    this.pushMsg({ id: this.uid(), role: 'user', time: this.now(), text });
  }

  private addBobMessage(text: string): void {
    this.pushMsg({ id: this.uid(), role: 'bob', time: this.now(), text });
  }

  private addStepsMessage(steps: PipelineStep[]): void {
    this.pushMsg({ id: this.uid(), role: 'bob', time: this.now(), steps });
  }

  private addSqlPreviewMessage(preview: SqlPreview): void {
    this.pushMsg({ id: this.uid(), role: 'bob', time: this.now(), sqlPreview: preview });
  }

  private addResultMessage(result: QueryResult): void {
    this.pushMsg({ id: this.uid(), role: 'bob', time: this.now(), results: result });
  }

  private addInsightsMessage(insights: Insight[]): void {
    this.pushMsg({ id: this.uid(), role: 'bob', time: this.now(), insights, showOutputSelector: true });
  }

  private addNextStepsMessage(nextSteps: string[]): void {
    this.pushMsg({ id: this.uid(), role: 'bob', time: this.now(), nextSteps });
  }

  // ── Atualiza status de um passo no pipeline ──────────────
  private updateStepStatus(label: string, status: PipelineStep['status']): void {
    this.messages.update(msgs =>
      msgs.map(m => {
        if (!m.steps) return m;
        return { ...m, steps: m.steps.map(s => s.label === label ? { ...s, status } : s) };
      })
    );
  }

  // ─────────────────────────────────────────────────────────
  //  Template helpers
  // ─────────────────────────────────────────────────────────
  formatCell(value: unknown, col: string): string {
    if (value == null) return '—';
    if (col.includes('revenue') || col.includes('cost')) {
      return '$ ' + Number(value).toLocaleString('en-US');
    }
    if (col === 'pct_change') {
      const n = Number(value);
      return (n > 0 ? '+' : '') + n.toFixed(1) + '%';
    }
    return String(value);
  }

  isNegative(value: unknown): boolean {
    return typeof value === 'number' && value < 0;
  }

  private pushMsg(m: ChatMessage): void {
    this.messages.update(msgs => [...msgs, m]);
  }

  private now(): string {
    return new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  }

  private uid(): string {
    return Math.random().toString(36).slice(2);
  }
}
