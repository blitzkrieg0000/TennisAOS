
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;


namespace DataAccess.Configurations {
    public class StreamConfiguration : IEntityTypeConfiguration<Entities.Concrete.Stream> {

        public void Configure(EntityTypeBuilder<Entities.Concrete.Stream> builder) {

            builder.ToTable("Stream");
            builder.HasKey(x=>x.Id);
            builder.Property(e => e.Id)
                .HasColumnName("id")
                .UseIdentityAlwaysColumn();

            builder.Property(e => e.CourtLineArray).HasColumnName("court_line_array");

            builder.Property(e => e.IsActivated)
                .IsRequired()
                .HasColumnName("is_activated")
                .HasDefaultValueSql("true");

            builder.Property(e => e.IsDeleted)
                .IsRequired()
                .HasColumnName("is_deleted")
                .HasDefaultValueSql("true");

            builder.Property(e => e.IsVideo).HasColumnName("is_video");

            builder.Property(e => e.Name).HasColumnName("name");

            builder.Property(e => e.PlayerId).HasColumnName("player_id");

            builder.Property(e => e.SaveDate)
                .HasColumnType("timestamp without time zone")
                .HasColumnName("save_date")
                .HasDefaultValueSql("CURRENT_TIMESTAMP");

            builder.Property(e => e.Source).HasColumnName("source");

            builder.HasOne(d => d.Player)
                .WithMany(p => p.Streams)
                .HasForeignKey(d => d.PlayerId)
                .OnDelete(DeleteBehavior.SetNull)
                .HasConstraintName("stream_fk");
        }
    }
}