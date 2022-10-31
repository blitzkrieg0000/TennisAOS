using Business.Interfaces;
using Dtos.CourtDtos;
using Entities.Concrete;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.Rendering;

namespace UI.ViewComponents {
    public class CourtSelectList : ViewComponent {

        private readonly IGenericService _genericService;

        public CourtSelectList(IGenericService genericService) {
            _genericService = genericService;
        }

        public async Task<IViewComponentResult> InvokeAsync() {
            var results = await _genericService.GetAll<CourtListDto, Court>();
            var data = new SelectList(results.Data, "Id", "Name", "CourtId");
            return View(data);
        }

    }
}