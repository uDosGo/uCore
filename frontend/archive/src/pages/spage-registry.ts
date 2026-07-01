/* Shared registry of S-page tool components for both main.tsx and USystemSurface */
import S100ToolBuilder from './S100ToolBuilder'
import S101StoryBuilder from './S101StoryBuilder'
import S300WorkflowBuilder from './S300WorkflowBuilder'
import S310ClipboardOrchestration from './S310ClipboardOrchestration'
import S320KnowledgeTools from './S320KnowledgeTools'
import S330MigrationDashboard from './S330MigrationDashboard'
import S600Learning from './S600Learning'

export const S_PAGE_COMPONENTS: Record<string, React.ComponentType> = {
  s100: S100ToolBuilder,
  s101: S101StoryBuilder,
  s300: S300WorkflowBuilder,
  s310: S310ClipboardOrchestration,
  s320: S320KnowledgeTools,
  s330: S330MigrationDashboard,
  s600: S600Learning,
}