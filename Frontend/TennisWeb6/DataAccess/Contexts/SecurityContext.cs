using DataAccess.Configurations;
using Entities.Concrete;
using Entities.Concrete.Security;
using Microsoft.AspNetCore.Identity.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore;

namespace DataAccess.Contexts {
    public class SecurityContext : IdentityDbContext<AppUser, AppRole, int> {

        public SecurityContext(DbContextOptions<SecurityContext> options) : base(options) {
            AppContext.SetSwitch("Npgsql.EnableLegacyTimestampBehavior", true);
        }
        
        public DbSet<AosType> Aostypes => this.Set<AosType>();
        public DbSet<Court> Courts => this.Set<Court>();
        public DbSet<CourtPointArea> CourtPointAreas => this.Set<CourtPointArea>();
        public DbSet<CourtType> CourtTypes => this.Set<CourtType>();
        public DbSet<Player> Players => this.Set<Player>();
        public DbSet<PlayingDatum> PlayingData => this.Set<PlayingDatum>();
        public DbSet<Entities.Concrete.Stream> Streams => this.Set<Entities.Concrete.Stream>();
        public DbSet<Gender> Genders => this.Set<Gender>();
        public DbSet<Session> Sessions => this.Set<Session>();
        public DbSet<SessionParameter> SessionParameters => this.Set<SessionParameter>();
        public DbSet<Process> Processes => this.Set<Process>();
        public DbSet<ProcessResponse> ProcessResponses => this.Set<ProcessResponse>();
        public DbSet<ProcessParameter> ProcessParameters => this.Set<ProcessParameter>();

        protected override void OnModelCreating(ModelBuilder modelBuilder) {
            modelBuilder.HasAnnotation("Relational:Collation", "en_US.utf8");

            modelBuilder.ApplyConfiguration(new AosTypeConfiguration());
            modelBuilder.ApplyConfiguration(new CourtConfiguration());
            modelBuilder.ApplyConfiguration(new CourtPointAreaConfiguration());
            modelBuilder.ApplyConfiguration(new CourtTypeConfiguration());
            modelBuilder.ApplyConfiguration(new PlayerConfiguration());
            modelBuilder.ApplyConfiguration(new PlayingDatumConfiguration());
            modelBuilder.ApplyConfiguration(new StreamConfiguration());
            modelBuilder.ApplyConfiguration(new GenderConfiguration());
            modelBuilder.ApplyConfiguration(new SessionConfiguration());
            modelBuilder.ApplyConfiguration(new SessionParameterConfiguration());
            modelBuilder.ApplyConfiguration(new ProcessConfiguration());
            modelBuilder.ApplyConfiguration(new ProcessResponseConfiguration());
            modelBuilder.ApplyConfiguration(new ProcessParameterConfiguration());
            base.OnModelCreating(modelBuilder);
        }
    }
}