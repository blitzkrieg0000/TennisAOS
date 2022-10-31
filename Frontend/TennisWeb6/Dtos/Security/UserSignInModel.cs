using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.Linq;
using System.Threading.Tasks;

namespace Dtos.Security {
    public class UserSignInModel {
        [Required(ErrorMessage = "Kullanıcı adı gereklidir.")]
        public string? Username { get; set; }

        [Required(ErrorMessage = "Parola gereklidir.")]
        public string? Password { get; set; }

        public bool RememberMe { get; set; }

        public string? ReturnUrl { get; set; }

    }
}