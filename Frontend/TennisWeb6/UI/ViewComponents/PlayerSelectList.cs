using Business.Interfaces;
using Dtos.PlayerDtos;
using Entities.Concrete;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.Rendering;

namespace UI.ViewComponents {
    public class PlayerSelectList : ViewComponent {

        private readonly IGenericService _genericService;

        public PlayerSelectList(IGenericService genericService) {
            _genericService = genericService;
        }

        public async Task<IViewComponentResult> InvokeAsync() {
            var results = await _genericService.GetAll<PlayerListDto, Player>();
            var data = new SelectList(results.Data, "Id", "Name", "PlayerId");
            return View(data);
        }

    }
}