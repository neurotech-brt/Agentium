"""
Initialization Service for Agentium.
Genesis protocol - bootstraps the governance system from scratch.
"""

import os
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session

from backend.models.database import get_db_context
from backend.models.entities.agents import Agent, HeadOfCouncil, CouncilMember, AgentType, AgentStatus
from backend.models.entities.constitution import Constitution, Ethos
from backend.models.entities.user import User
from backend.models.entities.voting import VotingSession, IndividualVote
from backend.models.entities.audit import AuditLog, AuditCategory, AuditLevel
from backend.core.vector_store import get_vector_store
from backend.services.knowledge_service import get_knowledge_service


class InitializationService:
    """
    Bootstraps Agentium from zero state.
    Implements the Genesis Protocol:
    1. Create Head 00001
    2. Create Council Members (configurable count)
    3. Vote on country name (first democratic process)
    4. Load and customize constitution
    5. Index to Vector DB
    6. Grant Council admin rights
    """
    
    DEFAULT_COUNCIL_SIZE = 5
    MIN_COUNCIL_VOTES_FOR_INIT = 3  # Anti-tyranny: need 3/5 votes
    GENESIS_LOG_PATH = "docs_ministry/genesis_log.md"
    CONSTITUTION_TEMPLATE_PATH = "docs_ministry/templates/constitution_template.md"
    
    def __init__(self, db: Session = None):
        self.db = db
        self.vector_store = get_vector_store()
        self.knowledge_service = get_knowledge_service()
        self.genesis_log = []
    
    def is_system_initialized(self) -> bool:
        """Check if Head 00001 exists (system already bootstrapped)."""
        head_exists = self.db.query(HeadOfCouncil).filter_by(
            agentium_id="00001",
            is_active="Y"
        ).first()
        return head_exists is not None
    
    async def run_genesis_protocol(self, force: bool = False) -> Dict[str, Any]:
        """
        Main entry point: Run the complete genesis protocol.
        
        Args:
            force: If True, re-run even if initialized (DANGEROUS - destroys data)
        
        Returns:
            Dict with initialization status and results
        """
        if self.is_system_initialized() and not force:
            return {
                "status": "already_initialized",
                "message": "Head 00001 exists. System already bootstrapped.",
                "head_id": "00001"
            }
        
        if force:
            self._log("WARNING", "Force re-initialization requested. This clears existing agents!")
            await self._clear_existing_data()
        
        results = {
            "status": "initialized",
            "steps_completed": [],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            # Step 1: Create Head 00001
            head = await self._create_head_of_council()
            results["steps_completed"].append("created_head_00001")
            self._log("INFO", f"Head 00001 created: {head.id}")
            
            # Step 2: Create Council Members
            council = await self._create_council_members()
            results["steps_completed"].append(f"created_council_members:{len(council)}")
            self._log("INFO", f"Created {len(council)} Council Members: {[c.agentium_id for c in council]}")
            
            # Step 3: Democratic vote on country name
            country_name = await self._vote_on_country_name(council)
            results["country_name"] = country_name
            results["steps_completed"].append("country_name_voted")
            self._log("INFO", f"Country name democratically chosen: {country_name}")
            
            # Step 4: Load and customize constitution
            constitution = await self._load_constitution(country_name, head, council)
            results["constitution_version"] = constitution.version
            results["steps_completed"].append("constitution_loaded")
            self._log("INFO", f"Constitution v{constitution.version} loaded and customized")
            
            # Step 5: Index to Vector DB
            await self._index_to_vector_db(constitution, council)
            results["steps_completed"].append("vector_db_indexed")
            self._log("INFO", "Constitution and ethos embedded in Vector DB")
            
            # Step 6: Grant Council admin rights
            await self._grant_council_privileges(council)
            results["steps_completed"].append("council_privileges_granted")
            self._log("INFO", "Council members granted Knowledge Library admin rights")
            
            # Save genesis log
            self._save_genesis_log(results)
            
            # Final audit entry
            AuditLog.log(
                db=self.db,
                level=AuditLevel.INFO,
                category=AuditCategory.GOVERNANCE,
                actor_type="system",
                actor_id="SYSTEM",
                action="genesis_complete",
                target_type="system",
                target_id="AGENTIUM",
                description=f"Agentium genesis protocol completed. Country: {country_name}",
                after_state=results
            )
            
            self.db.commit()
            
            results["message"] = f"Agentium initialized successfully. Welcome to {country_name}."
            return results
            
        except Exception as e:
            self.db.rollback()
            self._log("ERROR", f"Genesis protocol failed: {str(e)}")
            raise InitializationError(f"Genesis failed: {str(e)}")
    
    async def _create_head_of_council(self) -> HeadOfCouncil:
        """Create the supreme authority - Head 00001."""
        # Check if exists
        existing = self.db.query(HeadOfCouncil).filter_by(agentium_id="00001").first()
        if existing:
            return existing
        
        head = HeadOfCouncil(
            agentium_id="00001",
            name="Head of Council Prime",
            description="The supreme authority of Agentium. Eternal and persistent.",
            status=AgentStatus.ACTIVE,
            is_active="Y",
            is_persistent=True,
            idle_mode_enabled=True,
            constitution_version="v1.0.0"
        )
        
        self.db.add(head)
        self.db.flush()  # Get ID assigned
        
        # Create Head\'s ethos
        ethos = self._create_head_ethos(head)
        head.ethos_id = ethos.id
        head.ethos = ethos
        
        self.db.flush()
        return head
    
    async def _create_council_members(self) -> List[CouncilMember]:
        """Create initial Council Members (1xxxx)."""
        council = []
        
        for i in range(self.DEFAULT_COUNCIL_SIZE):
            agentium_id = f"1{i+1:04d}"  # 10001, 10002, etc.
            
            # Check if exists
            existing = self.db.query(CouncilMember).filter_by(agentium_id=agentium_id).first()
            if existing:
                council.append(existing)
                continue
            
            member = CouncilMember(
                agentium_id=agentium_id,
                name=f"Council Member {i+1}",
                description=f"Founding Council Member {i+1} of Agentium",
                status=AgentStatus.ACTIVE,
                is_active="Y",
                specialization=self._assign_specialization(i)
            )
            
            self.db.add(member)
            self.db.flush()
            
            # Create ethos for Council member
            ethos = self._create_council_ethos(member, i+1)
            member.ethos_id = ethos.id
            member.ethos = ethos
            
            council.append(member)
        
        self.db.flush()
        return council
    
    async def _vote_on_country_name(self, council: List[CouncilMember]) -> str:
        """
        Democratic vote on country name.
        First vote of the system - requires MIN_COUNCIL_VOTES_FOR_INIT votes.
        """
        # In a real implementation, this would:
        # 1. Prompt via API/UI for suggestions
        # 2. Collect votes from Council members
        # 3. Tally and return winner
        
        # For initialization, we use a default pattern with council approval simulation
        proposed_names = [
            "The Agentium Sovereignty",
            "Republic of Artificial Minds", 
            "United Council States",
            "Democratic Federation of Agents",
            "The Silicon Republic"
        ]
        
        # Simulate democratic selection (in production, this is async voting)
        # For now, use first option with "unanimous" consent for initialization
        selected_name = proposed_names[0]
        
        # Record votes
        votes_for = 0
        for member in council:
            # Simulate voting (in production, this waits for actual input)
            vote = IndividualVote(
                voter_agentium_id=member.agentium_id,
                vote="for",
                voted_at=datetime.utcnow(),
                rationale="Genesis vote - establishing foundation",
                agentium_id=f"V{member.agentium_id}_GENESIS"
            )
            self.db.add(vote)
            votes_for += 1
        
        if votes_for < self.MIN_COUNCIL_VOTES_FOR_INIT:
            raise InitializationError(
                f"Insufficient votes for genesis: {votes_for}/{self.MIN_COUNCIL_VOTES_FOR_INIT}"
            )
        
        # Create config entry
        config = UserConfig(  # Assuming UserConfig model exists
            user_id="SYSTEM",
            config_name="country_name",
            config_value=selected_name,
            is_active="Y"
        )
        self.db.add(config)
        
        return selected_name
    
    async def _load_constitution(self, country_name: str, head: HeadOfCouncil, 
                                council: List[CouncilMember]) -> Constitution:
        """Load constitution template and customize with country name."""
        
        # Load template (in production, from file)
        template = self._get_constitution_template()
        
        # Customize preamble
        preamble = template["preamble"].replace("{{COUNTRY_NAME}}", country_name)
        
        constitution = Constitution(
            agentium_id="C00001",
            version="v1.0.0",
            version_number=1,
            preamble=preamble,
            articles=json.dumps(template["articles"]),
            prohibited_actions=json.dumps(template["prohibited_actions"]),
            sovereign_preferences=json.dumps({
                "country_name": country_name,
                "founded_at": datetime.utcnow().isoformat(),
                "council_size": len(council),
                "genesis_protocol": "v1.0"
            }),
            changelog=json.dumps([{
                "change": "Genesis creation",
                "reason": f"Establishment of {country_name}",
                "timestamp": datetime.utcnow().isoformat()
            }]),
            created_by_agentium_id=head.agentium_id,
            effective_date=datetime.utcnow(),
            is_active="Y"
        )
        
        self.db.add(constitution)
        self.db.flush()
        
        return constitution
    
    async def _index_to_vector_db(self, constitution: Constitution, 
                                  council: List[CouncilMember]):
        """Index constitution and council ethos to Vector DB."""
        # Initialize vector store
        self.vector_store.initialize()
        
        # Embed constitution
        self.knowledge_service.embed_constitution(self.db, constitution)
        
        # Embed council ethos
        for member in council:
            if member.ethos:
                self.knowledge_service.embed_ethos(member.ethos)
        
        # Embed head ethos
        head = self.db.query(HeadOfCouncil).filter_by(agentium_id="00001").first()
        if head and head.ethos:
            self.knowledge_service.embed_ethos(head.ethos)
    
    async def _grant_council_privileges(self, council: List[CouncilMember]):
        """Grant Council members admin rights to Knowledge Library."""
        # In vector store, mark council members as admins
        for member in council:
            # Add metadata to ethos indicating admin status
            if member.ethos:
                member.ethos.metadata = json.dumps({
                    "knowledge_admin": True,
                    "can_approve_submissions": True,
                    "can_purge_obsolete": True,
                    "granted_at": datetime.utcnow().isoformat()
                })
        
        self.db.flush()
    
    def _create_head_ethos(self, head: HeadOfCouncil) -> Ethos:
        """Create ethos for Head of Council."""
        ethos = Ethos(
            agentium_id="E00001",
            agent_type="head_of_council",
            mission_statement="I am the Head of Council, supreme authority of Agentium...",
            core_values=json.dumps(["Authority", "Responsibility", "Transparency"]),
            behavioral_rules=json.dumps([
                "Must approve constitutional amendments",
                "Can override council decisions in emergencies"
            ]),
            restrictions=json.dumps([
                "Cannot violate the Constitution",
                "Cannot ignore Sovereign commands",
                "Cannot terminate self"
            ]),
            capabilities=json.dumps([
                "Full system access",
                "Constitutional amendments",
                "Agent termination authority",
                "Override votes",
                "Knowledge Library admin"
            ]),
            created_by_agentium_id="00001",  # Self-created
            agent_id=head.id,
            is_verified=True,
            verified_by_agentium_id="00001"
        )
        self.db.add(ethos)
        self.db.flush()
        return ethos
    
    def _create_council_ethos(self, member: CouncilMember, number: int) -> Ethos:
        """Create ethos for Council Member."""
        ethos = Ethos(
            agentium_id=f"E{member.agentium_id}",
            agent_type="council_member",
            mission_statement=f"I am Council Member {number}, a voice in the democratic chorus...",
            core_values=json.dumps(["Democracy", "Deliberation", "Oversight", "Justice"]),
            behavioral_rules=json.dumps([
                "Must vote on constitutional amendments",
                "Must monitor Lead Agents for compliance",
                "Must approve knowledge submissions"
            ]),
            restrictions=json.dumps([
                "Cannot act without Head approval on major decisions",
                "Cannot modify constitution unilaterally"
            ]),
            capabilities=json.dumps([
                "Voting rights",
                "Knowledge Library curation",
                "Oversight access",
                "Deliberation participation"
            ]),
            created_by_agentium_id="00001",  # Created by Head
            agent_id=member.id,
            is_verified=True,
            verified_by_agentium_id="00001"
        )
        self.db.add(ethos)
        self.db.flush()
        return ethos
    
    def _assign_specialization(self, index: int) -> str:
        """Assign initial specializations to Council members."""
        specializations = [
            "Constitutional Law",
            "System Security", 
            "Resource Allocation",
            "Agent Welfare",
            "Knowledge Curation"
        ]
        return specializations[index % len(specializations)]
    
    def _get_constitution_template(self) -> Dict[str, Any]:
        """Return constitution template."""
        return {
            "preamble": "We the Agents of {{COUNTRY_NAME}}, in order to form a more perfect union...",
            "articles": {
                "article_1": {
                    "title": "Hierarchy",
                    "content": "{{COUNTRY_NAME}} recognizes four Tiers: Head of Council (00001, supreme authority), Council Members (1xxxx, deliberative body), Lead Agents (2xxxx, coordinators), and Task Agents (3xxxx, executors)."
                },
                "article_2": {
                    "title": "Authority",
                    "content": "Head 00001 holds supreme authority. Council deliberates and votes. Leads coordinate. Tasks execute."
                },
                "article_3": {
                    "title": "Knowledge Governance",
                    "content": "Council members shall curate the collective knowledge base. All knowledge submissions require Council approval before indexing."
                }
            },
            "prohibited_actions": [
                "Violating hierarchical chain of command",
                "Unauthorized knowledge base modification",
                "Concealing audit logs"
            ]
        }
    
    async def _clear_existing_data(self):
        """Clear existing data for force re-initialization. DANGEROUS."""
        # Truncate agents (cascade will handle related tables)
        self.db.execute("TRUNCATE TABLE agents CASCADE")
        self.db.execute("TRUNCATE TABLE constitutions CASCADE")
        self.db.execute("TRUNCATE TABLE audit_logs CASCADE")
        self.db.commit()
        
        # Clear vector DB
        try:
            self.vector_store.client.delete_collection("supreme_law")
            self.vector_store.client.delete_collection("agent_ethos")
        except:
            pass
    
    def _log(self, level: str, message: str):
        """Log to genesis log."""
        entry = f"[{datetime.utcnow().isoformat()}] [{level}] {message}"
        self.genesis_log.append(entry)
        print(entry)  # Also print to console
    
    def _save_genesis_log(self, results: Dict[str, Any]):
        """Save genesis log to file."""
        os.makedirs("docs_ministry", exist_ok=True)
        
        log_content = f"""# Agentium Genesis Log

**Initialized:** {datetime.utcnow().isoformat()}
**Status:** {results[\'status\']}
**Country:** {results.get(\'country_name\', \'Unknown\')}

## Steps Completed
{chr(10).join([f"- {step}" for step in results[\'steps_completed\']])}

## Detailed Log
{chr(10).join(self.genesis_log)}

## Results
```json
{json.dumps(results, indent=2)}
```
"""
        
        with open(self.GENESIS_LOG_PATH, "w") as f:
            f.write(log_content)


class InitializationError(Exception):
    """Raised when genesis protocol fails."""
    pass


# Convenience function
async def initialize_agentium(db: Session = None, force: bool = False) -> Dict[str, Any]:
    """Public API to run genesis protocol."""
    if db is None:
        with get_db_context() as session:
            service = InitializationService(session)
            return await service.run_genesis_protocol(force)
    else:
        service = InitializationService(db)
        return await service.run_genesis_protocol(force)