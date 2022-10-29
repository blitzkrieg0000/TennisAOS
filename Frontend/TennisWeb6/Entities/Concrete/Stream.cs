namespace Entities.Concrete {
    public class Stream : BaseEntity {
        public Stream() {
            PlayingData = new HashSet<PlayingDatum>();
            ProcessParameters = new HashSet<ProcessParameter>();
            SessionParameters = new HashSet<SessionParameter>();
        }

        public long Id { get; set; }
        public string Name { get; set; } = null!;
        public string Source { get; set; } = null!;
        public string? CourtLineArray { get; set; }
        public DateTime SaveDate { get; set; }
        public bool? IsActivated { get; set; }
        public bool? IsDeleted { get; set; }
        public bool IsVideo { get; set; }
        public long? PlayerId { get; set; }

        public virtual Player? Player { get; set; }
        public virtual ICollection<PlayingDatum> PlayingData { get; set; }
        public virtual ICollection<ProcessParameter> ProcessParameters { get; set; }
        public virtual ICollection<SessionParameter> SessionParameters { get; set; }
    }
}
