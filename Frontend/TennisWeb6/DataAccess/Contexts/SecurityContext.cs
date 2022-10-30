using Entities.Concrete.Security;
using Microsoft.AspNetCore.Identity.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore;

namespace DataAccess.Contexts {
    public class SecurityContext : IdentityDbContext<AppUser, AppRole, int> {

        public SecurityContext(DbContextOptions<SecurityContext> options) : base(options) {
        }

    }
}