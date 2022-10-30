using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Identity;

namespace Entities.Concrete.Security {
    public class AppRole : IdentityRole<int> {

        public DateTime CreatedTime { get; set; }

    }
}